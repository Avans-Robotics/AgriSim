// Pull-out of picked Plants (ADR 0006): a world system that, on a pick request, removes the
// Plant's grouped visual, spawns its articulated model, welds the root to an anchor on a
// vertical prismatic joint and applies the Pull-out Curve as the joint force every step until
// the root has travelled its root depth, then detaches it. Any number of Plants can be picked
// at once, each Plant id once. After the peak the anchor's lower limit follows the highest
// point reached, so a released, part-pulled root stays where it is.
//
// Pick service /world/<world>/pixelfield/pick: gz.msgs.EntityFactory (sdf_filename, name = Plant
// id, pose) replied with gz.msgs.Boolean. The Plant SDF carries the curve as a custom element
// <pixelfield:pull_out f_peak d_peak residual_fraction damping depth/> in its model.
// State topic /world/<world>/pixelfield/pull_out: gz.msgs.Param with plant, d, force, attached.

#include <algorithm>
#include <map>
#include <mutex>
#include <set>
#include <string>
#include <vector>

#include <gz/msgs/boolean.pb.h>
#include <gz/msgs/entity_factory.pb.h>
#include <gz/msgs/param.pb.h>
#include <gz/msgs/Utility.hh>
#include <gz/plugin/Register.hh>
#include <gz/sim/Conversions.hh>
#include <gz/sim/Link.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/SdfEntityCreator.hh>
#include <gz/sim/System.hh>
#include <gz/sim/World.hh>
#include <gz/sim/components/CollisionBitmask.hh>
#include <gz/sim/components/DetachableJoint.hh>
#include <gz/sim/components/JointForceCmd.hh>
#include <gz/sim/components/JointPositionLimitsCmd.hh>
#include <gz/sim/components/JointPosition.hh>
#include <gz/sim/components/JointVelocity.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/transport/Node.hh>
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

struct Request
{
  std::string name;
  gz::math::Pose3d pose;
  sdf::Model model;
  Curve curve;
};

struct Pick
{
  std::string name;
  Curve curve;
  Entity anchor, slide, weld, root;
  bool broken = false;
  bool detached = false;
  double held = 0.0;  // lower limit of the slide: the highest d reached after the peak
};

class PullOut : public System, public ISystemConfigure, public ISystemPreUpdate
{
  public: void Configure(const Entity &_entity, const std::shared_ptr<const sdf::Element> &,
                         EntityComponentManager &_ecm, EventManager &_eventMgr) override
  {
    this->world = _entity;
    this->eventMgr = &_eventMgr;
    const std::string prefix = "/world/" + World(_entity).Name(_ecm).value_or("") + "/pixelfield";
    this->node.Advertise(prefix + "/pick", &PullOut::OnPick, this);
    this->state = this->node.Advertise<gz::msgs::Param>(prefix + "/pull_out");
  }

  /// Runs in a transport thread: parse and check only, the ECM is touched in PreUpdate. The
  /// reply is true only for a request that PreUpdate will spawn.
  private: bool OnPick(const gz::msgs::EntityFactory &_req, gz::msgs::Boolean &_rep)
  {
    _rep.set_data(false);
    const std::string &name = _req.name();
    auto root = std::make_shared<sdf::Root>();
    auto errors = root->Load(_req.sdf_filename());
    if (!errors.empty() || root->Model() == nullptr ||
        root->Model()->LinkByName("root") == nullptr)
    {
      gzerr << "Pick: [" << _req.sdf_filename() << "] is not a Plant model with a root link\n";
      return true;
    }
    auto element = root->Model()->Element()->FindElement("pixelfield:pull_out");
    double value[5];
    const char *keys[] = {"f_peak", "d_peak", "residual_fraction", "damping", "depth"};
    for (int i = 0; i < 5; ++i)
    {
      if (!element || !element->HasAttribute(keys[i]))
      {
        gzerr << "Pick: no <pixelfield:pull_out " << keys[i] << "> in ["
              << _req.sdf_filename() << "]\n";
        return true;
      }
      value[i] = element->Get<double>(keys[i]);
    }
    Curve curve{value[0], value[1], value[2], value[3], value[4]};
    if (!(curve.fPeak > 0 && curve.dPeak > 0 && curve.dPeak < curve.depth &&
          curve.residual >= 0 && curve.residual <= 1 && curve.damping >= 0))
    {
      gzerr << "Pick: invalid Pull-out Curve in [" << _req.sdf_filename() << "]\n";
      return true;
    }
    std::lock_guard<std::mutex> lock(this->mutex);
    if (name.find('-') == std::string::npos || this->picked.count(name))
    {
      gzerr << "Pick: [" << name << "] is not a Plant id or was already picked\n";
      return true;
    }
    sdf::Model model = *root->Model();
    model.SetName(name);
    this->requests.push_back(Request{name, gz::msgs::Convert(_req.pose()), model, curve});
    this->picked.insert(name);
    // ponytail: one sdf::Root kept per pick (a few kB, the entities may refer to its graphs);
    // free them on world reset if long training runs pick thousands of Plants.
    this->roots.push_back(root);
    _rep.set_data(true);
    return true;
  }

  public: void PreUpdate(const UpdateInfo &_info, EntityComponentManager &_ecm) override
  {
    std::lock_guard<std::mutex> lock(this->mutex);
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
    p.broken = p.broken || d >= p.curve.dPeak;  // the soil bond does not come back
    if (p.broken && d > p.held)
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
    }

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

    SdfEntityCreator creator(_ecm, *this->eventMgr);
    Entity plant = creator.CreateEntities(&_r.model);
    creator.SetParent(plant, this->world);
    _ecm.SetComponentData<components::Pose>(plant, _r.pose);
    Entity root = Model(plant).LinkByName(_ecm, "root");

    // Anchor at the root's world position, unrotated, so the joint axis is world z.
    auto at = (_r.pose * _r.model.LinkByName("root")->RawPose()).Pos();
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
  private: std::mutex mutex;
  private: std::vector<Request> requests;
  private: std::map<std::string, Pick> picks;
  private: std::set<std::string> picked;
  private: std::vector<std::shared_ptr<sdf::Root>> roots;
};
}  // namespace pixelfield

GZ_ADD_PLUGIN(pixelfield::PullOut, gz::sim::System, gz::sim::ISystemConfigure,
              gz::sim::ISystemPreUpdate)
