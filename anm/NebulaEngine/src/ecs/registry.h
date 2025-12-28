#pragma once
#include <vector>
#include "../core/types.h"
#include "components.h"

namespace ne {

// Minimal internal ECS: SoA arrays keyed by Entity id.
class Registry {
public:
    Entity create();

    void add_transform(Entity e, const Transform& t);
    void add_velocity (Entity e, const Velocity& v);
    void add_mass     (Entity e, const Mass& m);
    void add_force    (Entity e, const Force& f);
    void add_sphere   (Entity e, const Sphere& s);
    void add_aabb     (Entity e, const AABB& a);

    bool has_alive(Entity e) const;
    bool has_sphere(Entity e) const;
    bool has_aabb(Entity e) const;

    // Accessors (unsafe if missing; v0 simplicity)
    Transform& transform(Entity e);
    Velocity&  velocity(Entity e);
    Mass&      mass(Entity e);
    Force&     force(Entity e);
    Sphere&    sphere(Entity e);
    AABB&      aabb(Entity e);

    // Const accessors
    const Transform& transform(Entity e) const;
    const Velocity&  velocity(Entity e) const;
    const Mass&      mass(Entity e) const;
    const Force&     force(Entity e) const;
    const Sphere&    sphere(Entity e) const;
    const AABB&      aabb(Entity e) const;

    // Iteration helpers
    const std::vector<Entity>& alive() const { return m_alive; }

    // Component accessors for iteration
    std::vector<Transform>& transforms() { return m_t; }
    std::vector<Velocity>& velocities() { return m_v; }
    std::vector<Mass>& masses() { return m_m; }
    std::vector<Force>& forces() { return m_f; }
    std::vector<Sphere>& spheres() { return m_spheres; }
    std::vector<AABB>& aabbs() { return m_aabbs; }

private:
    void ensure(Entity e);

    Entity m_next = 1;
    std::vector<Entity> m_alive;

    std::vector<bool>      m_exists;
    std::vector<bool>      m_has_sphere;
    std::vector<bool>      m_has_aabb;
    std::vector<Transform> m_t;
    std::vector<Velocity>  m_v;
    std::vector<Mass>      m_m;
    std::vector<Force>     m_f;
    std::vector<Sphere>    m_spheres;
    std::vector<AABB>      m_aabbs;
};

} // namespace ne