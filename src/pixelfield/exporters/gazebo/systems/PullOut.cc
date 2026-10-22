// Pull-out of picked Plants (ADR 0006): a world system that, on a pick request, removes the
// Plant's grouped visual, spawns its articulated model, welds the root to an anchor on a
// vertical prismatic joint and applies the Pull-out Curve as the joint force every step until
// the root has travelled its root depth, then detaches it. Any number of Plants can be picked
// at once, each Plant id once. After the peak the anchor's lower limit follows the highest
// point reached, so a released, part-pulled root stays where it is.
//
// `pixelfield build` writes next to the world plants/<id>.sdf for every root crop Plant (its
// model at its pose, with the curve as a custom element <pixelfield:pull_out f_peak d_peak
// residual_fraction damping depth/>) and the table plants/plants.tsv (id, x, y, z, footprint
// radius and height, crown radius), read on the first update (ADR 0010).
// Pick service /world/<world>/pixelfield/pick: gz.msgs.StringMsg with the Plant id, replied
// with gz.msgs.Boolean.
// Active Region (ADR 0010): every 10 ms of sim time, each link with collisions of a model that
// is not part of the Field (soil, Pixel models r<row>c<col>, camera_* models, Picked Plants
// and their anchors) takes its world axis-aligned box plus <padding> meters (default 0.05).
// Every root crop Plant whose footprint meets that box is picked like a pick by id. The
// footprint is a vertical cylinder from the Plant's z up to its foliage height, around its
// crown with the crown radius, or with the foliage radius when <footprint> is "foliage".
// State topic /world/<world>/pixelfield/pull_out: gz.msgs.Param with plant, d, force, attached,
// published only on a step where d or the force changed, plus one message per event, which
// also carries `event`: picked, peak_passed or detached. A resting Picked Plant is silent.

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <map>
#include <mutex>
#include <optional>
#include <regex>
#include <set>
#include <string>
#include <unordered_map>
#include <vector>

#include <gz/msgs/boolean.pb.h>
#include <gz/msgs/param.pb.h>
#include <gz/msgs/stringmsg.pb.h>
#include <gz/plugin/Register.hh>
#include <gz/sim/Conversions.hh>
#include <gz/sim/Link.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/SdfEntityCreator.hh>
#include <gz/sim/System.hh>
#include <gz/sim/Util.hh>
#include <gz/sim/World.hh>
#include <gz/sim/components/Collision.hh>
#include <gz/sim/components/CollisionBitmask.hh>
#include <gz/sim/components/DetachableJoint.hh>
#include <gz/sim/components/JointForceCmd.hh>
#include <gz/sim/components/JointPositionLimitsCmd.hh>
#include <gz/sim/components/JointPosition.hh>
#include <gz/sim/components/JointVelocity.hh>
#include <gz/sim/components/Link.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/transport/Node.hh>
#include <sdf/Collision.hh>
#include <sdf/Geometry.hh>
#include <sdf/Link.hh>
#include <sdf/Model.hh>
#include <sdf/Root.hh>

namespace pixelfield
{
using namespace gz::sim;

constexpr uint16_t kAllBits = 0xFFFF;  // collide bitmask of a detached root
constexpr double kAnchorMass = 0.001;  // kg, light next to any root
// The prismatic range ends a little past the root depth so the joint limit never stops the
// root before it reaches the detach point.
constexpr double kRangeMargin = 0.01;  // meters
// A state message goes out once d or the force has moved this far from the last one sent. At
// rest both repeat to the last bit (measured on a ratchet-held root); a 5 cm/s pull moves d
// about 10 um per step.
constexpr double kQuietD = 1e-9;  // meters
constexpr double kQuietForce = 1e-6;  // newtons
constexpr std::chrono::milliseconds kRegionPeriod{10};  // sim time between Active Region checks
const std::regex kPixelName("r[0-9]+c[0-9]+");  // Pixel models, ADR 0007

struct Curve
{
  double fPeak, dPeak, residual, damping, depth;
};

/// Resisting force of the soil in newtons (positive pulls the root down), ADR 0006.
double Resistance(const Curve &_c, bool _broken, double _d, double _v)
{
  double f = _broken
    ? _c.residual * _c.fPeak * (_c.depth - std::max(_d, _c.dPeak)) / (_c.depth - _c.dPeak)
    : _c.fPeak * std::max(_d, 0.0) / _c.dPeak;
  return std::max(f, 0.0) + _c.damping * _v;
}

/// The 8 corners of a box moved by a pose, boxed again: it holds everything the box held.
gz::math::AxisAlignedBox Moved(const gz::math::AxisAlignedBox &_box,
                               const gz::math::Pose3d &_pose)
{
  const gz::math::Vector3d &a = _box.Min(), &b = _box.Max();
  gz::math::Vector3d lo(gz::math::MAX_D, gz::math::MAX_D, gz::math::MAX_D), hi = -lo;
  for (int i = 0; i < 8; ++i)
  {
    gz::math::Vector3d corner = _pose.CoordPositionAdd(
      {i & 1 ? b.X() : a.X(), i & 2 ? b.Y() : a.Y(), i & 4 ? b.Z() : a.Z()});
    lo.Min(corner);
    hi.Max(corner);
  }
  return {lo, hi};
}

/// A link's box in its own frame, from its collisions; nullopt without any. Not gz-sim's
/// Link::ComputeAxisAlignedBox: it moves only two corners of each collision's box, so a
/// collision turned in its link comes out too small (a cube turned 45 degrees about z gets no
/// width in x).
std::optional<gz::math::AxisAlignedBox> LinkBox(Entity _link, const EntityComponentManager &_ecm)
{
  std::optional<gz::math::AxisAlignedBox> box;
  for (Entity collision : Link(_link).Collisions(_ecm))
  {
    auto element = _ecm.Component<components::CollisionElement>(collision);
    auto pose = _ecm.Component<components::Pose>(collision);
    if (!element || !element->Data().Geom())
      continue;
    auto local = element->Data().Geom()->AxisAlignedBox(&meshAxisAlignedBox);
    if (!local || !(local->Min().X() <= local->Max().X()))
      continue;  // no size, or an empty box that would span everything once moved
    auto moved = Moved(*local, pose ? pose->Data() : gz::math::Pose3d::Zero);
    box = box ? *box + moved : moved;
  }
  return box;
}

struct Request
{
  std::string name;
  sdf::Model model;
  Curve curve;
};

/// A row of plants/plants.tsv: the Plant's position and its footprint for the Active Region.
struct Footprint
{
  gz::math::Vector3d position;
  double radius, height, crown;  // foliage radius, foliage height, crown radius
};

struct Pick
{
  std::string name;
  Curve curve;
  Entity anchor, slide, weld, root;
  bool broken = false;
  bool detached = false;
  bool announced = false;  // the picked event went out
  double held = 0.0;  // lower limit of the slide: the highest d reached after the peak
  double sentD = 0.0, sentForce = 0.0;  // last published state
};

class PullOut : public System, public ISystemConfigure, public ISystemPreUpdate
{
  public: void Configure(const Entity &_entity, const std::shared_ptr<const sdf::Element> &_sdf,
                         EntityComponentManager &_ecm, EventManager &_eventMgr) override
  {
    this->world = _entity;
    this->padding = _sdf->Get<double>("padding", this->padding).first;
    this->foliage = _sdf->Get<std::string>("footprint", "crown").first == "foliage";
    this->eventMgr = &_eventMgr;
    const std::string prefix = "/world/" + World(_entity).Name(_ecm).value_or("") + "/pixelfield";
    this->node.Advertise(prefix + "/pick", &PullOut::OnPick, this);
    this->state = this->node.Advertise<gz::msgs::Param>(prefix + "/pull_out");
  }

  /// Reads plants/plants.tsv next to the world file. Plugin elements lose their file path in
  /// gz-sim, so the path comes from the soil model, which is defined in the world file and
  /// exists from the first update on (not yet in Configure).
  private: void LoadTable(EntityComponentManager &_ecm)
  {
    Model soil(World(this->world).ModelByName(_ecm, "soil"));
    this->dir = std::filesystem::path(soil.SourceFilePath(_ecm)).parent_path() / "plants";
    std::ifstream table(this->dir / "plants.tsv");
    std::string id, header;
    std::getline(table, header);
    Footprint f;
    while (table >> id >> f.position.X() >> f.position.Y() >> f.position.Z() >> f.radius >>
           f.height >> f.crown)
      this->plants[id] = f;
    if (this->plants.empty())
      gzwarn << "PullOut: no Plants in [" << (this->dir / "plants.tsv").string()
             << "], nothing can be picked (a Field without root crops, or built before M5d)\n";
  }

  /// Runs in a transport thread: parse and check only, the ECM is touched in PreUpdate. The
  /// reply is true only for a request that PreUpdate will spawn.
  private: bool OnPick(const gz::msgs::StringMsg &_req, gz::msgs::Boolean &_rep)
  {
    _rep.set_data(false);
    const std::string &name = _req.data();
    std::unique_lock<std::mutex> lock(this->mutex);
    if (!this->loaded)
    {
      gzerr << "Pick: [" << name << "] refused, the world is still loading; try again\n";
      return true;
    }
    if (!this->plants.count(name))
    {
      gzerr << "Pick: [" << name << "] is not a root crop Plant of this Field\n";
      return true;
    }
    lock.unlock();  // parse the file without blocking the simulation
    auto request = this->Load(name);
    lock.lock();
    if (!request)
      return true;
    if (this->picked.count(name))
    {
      gzerr << "Pick: [" << name << "] was already picked\n";
      return true;
    }
    this->requests.push_back(*request);
    this->picked.insert(name);
    _rep.set_data(true);
    return true;
  }

  /// Parses plants/<name>.sdf into a request; nullopt (and an error) if it is not a Plant.
  /// Touches no shared state but `roots`, under the caller's lock when it adds one.
  private: std::optional<Request> Load(const std::string &_name)
  {
    const std::string file = (this->dir / (_name + ".sdf")).string();
    auto root = std::make_shared<sdf::Root>();
    auto errors = root->Load(file);
    if (!errors.empty() || root->Model() == nullptr ||
        root->Model()->LinkByName("root") == nullptr)
    {
      gzerr << "Pick: [" << file << "] is not a Plant model with a root link\n";
      return std::nullopt;
    }
    auto element = root->Model()->Element()->FindElement("pixelfield:pull_out");
    double value[5];
    const char *keys[] = {"f_peak", "d_peak", "residual_fraction", "damping", "depth"};
    for (int i = 0; i < 5; ++i)
    {
      if (!element || !element->HasAttribute(keys[i]))
      {
        gzerr << "Pick: no <pixelfield:pull_out " << keys[i] << "> in [" << file << "]\n";
        return std::nullopt;
      }
      value[i] = element->Get<double>(keys[i]);
    }
    Curve curve{value[0], value[1], value[2], value[3], value[4]};
    if (!(curve.fPeak > 0 && curve.dPeak > 0 && curve.dPeak < curve.depth &&
          curve.residual >= 0 && curve.residual <= 1 && curve.damping >= 0))
    {
      gzerr << "Pick: invalid Pull-out Curve in [" << file << "]\n";
      return std::nullopt;
    }
    std::lock_guard<std::mutex> lock(this->rootsMutex);
    // ponytail: one sdf::Root kept per pick (a few kB, the entities may refer to its graphs);
    // free them on world reset if long training runs pick thousands of Plants.
    this->roots.push_back(root);
    return Request{_name, *root->Model(), curve};
  }

  /// Field models never trigger the Active Region; everything else in the world does.
  private: bool IsField(const std::string &_model) const
  {
    const std::string anchor = "_anchor";
    bool isAnchor = _model.size() > anchor.size() &&
      _model.compare(_model.size() - anchor.size(), anchor.size(), anchor) == 0 &&
      this->plants.count(_model.substr(0, _model.size() - anchor.size()));
    return _model == "soil" || _model.rfind("camera_", 0) == 0 ||
      std::regex_match(_model, kPixelName) || this->plants.count(_model) || isAnchor;
  }

  /// One Active Region check: picks every Plant whose footprint meets a non-Field link's box.
  private: void Region(EntityComponentManager &_ecm)
  {
    std::vector<std::string> hits;
    _ecm.Each<components::Link>([&](const Entity &_link, const components::Link *) -> bool
    {
      auto cached = this->boxes.find(_link);
      if (cached == this->boxes.end())
      {
        // A link's box in its own frame only changes with its collisions: computed once.
        std::optional<gz::math::AxisAlignedBox> box;
        if (!this->IsField(Model(topLevelModel(_link, _ecm)).Name(_ecm)))
          box = LinkBox(_link, _ecm);
        cached = this->boxes.emplace(_link, box).first;
      }
      if (!cached->second)
        return true;
      // The world box of the link's box: larger than the link when it is turned, so it picks
      // a few Plants too many, never too few.
      gz::math::AxisAlignedBox world = Moved(*cached->second, worldPose(_link, _ecm));
      const gz::math::Vector3d lo = world.Min() - gz::math::Vector3d::One * this->padding;
      const gz::math::Vector3d hi = world.Max() + gz::math::Vector3d::One * this->padding;
      // ponytail: every Plant against every link, about 150k cheap tests per check on a
      // 10 x 10 Field with a robot; bucket the table per Pixel if Fields or robots grow.
      for (const auto &[id, f] : this->plants)
      {
        const gz::math::Vector3d &p = f.position;
        double r = this->foliage ? f.radius : f.crown;
        double dx = std::max({lo.X() - p.X(), 0.0, p.X() - hi.X()});
        double dy = std::max({lo.Y() - p.Y(), 0.0, p.Y() - hi.Y()});
        if (p.Z() <= hi.Z() && p.Z() + f.height >= lo.Z() && dx * dx + dy * dy <= r * r &&
            !this->picked.count(id))
          hits.push_back(id);
      }
      return true;
    });
    for (const std::string &id : hits)
    {
      if (this->picked.count(id))
        continue;  // met by two links
      this->picked.insert(id);  // also when its file is broken: one error, not one per check
      // ponytail: parsed in the simulation thread, a few ms per Plant; move it to a worker
      // if a robot reaching into a bed stalls the simulation noticeably.
      if (auto request = this->Load(id))
        this->requests.push_back(*request);
    }
  }

  public: void PreUpdate(const UpdateInfo &_info, EntityComponentManager &_ecm) override
  {
    std::lock_guard<std::mutex> lock(this->mutex);
    if (!this->loaded)
    {
      this->LoadTable(_ecm);
      this->loaded = true;
    }
    if (!_info.paused && _info.simTime - this->lastRegion >= kRegionPeriod)
    {
      this->lastRegion = _info.simTime;
      this->Region(_ecm);
    }
    for (const Request &r : this->requests)
      this->Spawn(r, _ecm);
    this->requests.clear();
    if (_info.paused)
      return;
    for (auto it = this->picks.begin(); it != this->picks.end();)
      it = this->Step(it->second, _info, _ecm) ? std::next(it) : this->picks.erase(it);
  }

  /// One physics step of one picked Plant; false once it is done.
  private: bool Step(Pick &p, const UpdateInfo &_info, EntityComponentManager &_ecm)
  {
    if (p.detached)
    {
      // A step after the weld: removing both at once also removes the root, which dartsim
      // keeps in the anchor's skeleton until the weld is gone.
      _ecm.RequestRemoveEntity(p.anchor, true);
      return false;
    }
    auto position = _ecm.Component<components::JointPosition>(p.slide);
    auto velocity = _ecm.Component<components::JointVelocity>(p.slide);
    if (!position || position->Data().empty() || !velocity || velocity->Data().empty())
      return true;  // filled by Physics from the step after the spawn
    double d = position->Data()[0], v = velocity->Data()[0];
    const char *event = p.announced ? nullptr : "picked";
    p.announced = true;
    if (!p.broken && d >= p.curve.dPeak)
    {
      p.broken = true;  // the soil bond does not come back
      event = "peak_passed";
    }
    // Not on the detach step: a fast pull can jump past the slide's upper limit, and a lower
    // limit above the upper one aborts dartsim.
    if (p.broken && d > p.held && d < p.curve.depth)
    {
      // Ratchet: a loosened root is held by friction, the residual force must not push it back.
      p.held = d;
      std::vector<gz::math::Vector2d> limits{{p.held, p.curve.depth + kRangeMargin}};
      auto cmd = _ecm.Component<components::JointPositionLimitsCmd>(p.slide);
      if (cmd)
        cmd->Data() = limits;
      else
        _ecm.CreateComponent(p.slide, components::JointPositionLimitsCmd(limits));
    }
    bool attached = d < p.curve.depth;
    double force = attached ? Resistance(p.curve, p.broken, d, v) : 0.0;
    if (attached)
    {
      auto cmd = _ecm.Component<components::JointForceCmd>(p.slide);
      if (cmd)
        cmd->Data() = {-force};
      else
        _ecm.CreateComponent(p.slide, components::JointForceCmd({-force}));
    }
    else
    {
      _ecm.RequestRemoveEntity(p.weld);
      // The root left out the soil's collide bit while buried; out of the soil it may land on it.
      for (Entity collision : Link(p.root).Collisions(_ecm))
        _ecm.CreateComponent(collision, components::CollideBitmaskCmd(kAllBits));
      p.detached = true;
      event = "detached";
    }
    if (!event && std::abs(d - p.sentD) <= kQuietD && std::abs(force - p.sentForce) <= kQuietForce)
      return true;  // resting: silent
    p.sentD = d;
    p.sentForce = force;

    gz::msgs::Param msg;
    msg.mutable_header()->mutable_stamp()->CopyFrom(convert<gz::msgs::Time>(_info.simTime));
    auto &params = *msg.mutable_params();
    params["plant"].set_type(gz::msgs::Any::STRING);
    params["plant"].set_string_value(p.name);
    params["d"].set_type(gz::msgs::Any::DOUBLE);
    params["d"].set_double_value(d);
    params["force"].set_type(gz::msgs::Any::DOUBLE);
    params["force"].set_double_value(force);
    params["attached"].set_type(gz::msgs::Any::BOOLEAN);
    params["attached"].set_bool_value(attached);
    if (event)
    {
      params["event"].set_type(gz::msgs::Any::STRING);
      params["event"].set_string_value(event);
    }
    this->state.Publish(msg);
    return true;
  }

  private: void Spawn(const Request &_r, EntityComponentManager &_ecm)
  {
    World world(this->world);
    if (world.ModelByName(_ecm, _r.name) != kNullEntity)
    {
      gzerr << "Pick: [" << _r.name << "] is already a model\n";
      return;
    }
    // Plants are visuals of their Pixel's model r<row>c<col> (ADR 0007), ids r<row>c<col>-<n>.
    Model pixel(world.ModelByName(_ecm, _r.name.substr(0, _r.name.find('-'))));
    bool removed = false;
    for (Entity link : pixel.Links(_ecm))
    {
      Entity visual = Link(link).VisualByName(_ecm, _r.name);
      if (visual != kNullEntity)
      {
        _ecm.RequestRemoveEntity(visual);
        removed = true;
      }
    }
    if (!removed)
      gzwarn << "Pick: no grouped visual [" << _r.name << "] to remove\n";

    // The model's pose in its file is the Plant's pose in the Field.
    SdfEntityCreator creator(_ecm, *this->eventMgr);
    Entity plant = creator.CreateEntities(&_r.model);
    creator.SetParent(plant, this->world);
    _ecm.SetComponentData<components::Pose>(plant, _r.model.RawPose());
    Entity root = Model(plant).LinkByName(_ecm, "root");

    // Anchor at the root's world position, unrotated, so the joint axis is world z.
    auto at = (_r.model.RawPose() * _r.model.LinkByName("root")->RawPose()).Pos();
    const std::string anchorSdf =
      "<sdf version='1.9'><model name='" + _r.name + "_anchor'><pose>" +
      std::to_string(at.X()) + " " + std::to_string(at.Y()) + " " + std::to_string(at.Z()) +
      " 0 0 0</pose><link name='anchor'><inertial><mass>" + std::to_string(kAnchorMass) +
      "</mass><inertia><ixx>1e-7</ixx><iyy>1e-7</iyy><izz>1e-7</izz></inertia></inertial>"
      "</link><joint name='slide' type='prismatic'><parent>world</parent><child>anchor</child>"
      "<axis><xyz>0 0 1</xyz><limit><lower>0</lower><upper>" +
      std::to_string(_r.curve.depth + kRangeMargin) + "</upper></limit></axis></joint>"
      "</model></sdf>";
    sdf::Root anchorRoot;
    anchorRoot.LoadSdfString(anchorSdf);
    Entity anchor = creator.CreateEntities(anchorRoot.Model());
    creator.SetParent(anchor, this->world);
    Model anchorModel(anchor);
    Entity slide = anchorModel.JointByName(_ecm, "slide");
    _ecm.CreateComponent(slide, components::JointPosition());
    _ecm.CreateComponent(slide, components::JointVelocity());

    Entity weld = _ecm.CreateEntity();
    _ecm.CreateComponent(weld, components::DetachableJoint(
      {anchorModel.LinkByName(_ecm, "anchor"), root, "fixed"}));
    this->picks[_r.name] = Pick{_r.name, _r.curve, anchor, slide, weld, root};
    gzmsg << "Pick: [" << _r.name << "] spawned and anchored\n";
  }

  private: Entity world{kNullEntity};
  private: EventManager *eventMgr{nullptr};
  private: gz::transport::Node node;
  private: gz::transport::Node::Publisher state;
  private: bool loaded = false;  // the table, on the first update
  private: std::filesystem::path dir;  // plants/ next to the world file
  private: std::map<std::string, Footprint> plants;
  private: std::mutex mutex;
  private: std::vector<Request> requests;
  private: std::map<std::string, Pick> picks;
  private: std::set<std::string> picked;
  private: std::mutex rootsMutex;  // Load runs in the transport thread and in PreUpdate
  private: std::vector<std::shared_ptr<sdf::Root>> roots;
  private: double padding = 0.05;  // meters around each link's box
  private: bool foliage = false;  // footprint radius: foliage instead of crown
  private: std::chrono::steady_clock::duration lastRegion{-kRegionPeriod};
  private: std::unordered_map<Entity, std::optional<gz::math::AxisAlignedBox>> boxes;
};
}  // namespace pixelfield

GZ_ADD_PLUGIN(pixelfield::PullOut, gz::sim::System, gz::sim::ISystemConfigure,
              gz::sim::ISystemPreUpdate)
