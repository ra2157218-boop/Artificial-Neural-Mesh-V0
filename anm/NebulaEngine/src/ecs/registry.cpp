#include "registry.h"
#include <cassert>

namespace ne {

void Registry::ensure(Entity e) {
    const std::size_t idx = static_cast<std::size_t>(e);
    if (idx >= m_exists.size()) {
        m_exists.resize(idx + 1, false);
        m_has_sphere.resize(idx + 1, false);
        m_has_aabb.resize(idx + 1, false);
        m_t.resize(idx + 1);
        m_v.resize(idx + 1);
        m_m.resize(idx + 1);
        m_f.resize(idx + 1);
        m_spheres.resize(idx + 1);
        m_aabbs.resize(idx + 1);
    }
}

Entity Registry::create() {
    Entity e = m_next++;
    ensure(e);
    m_exists[e] = true;
    m_alive.push_back(e);
    return e;
}

bool Registry::has_alive(Entity e) const {
    return e < m_exists.size() && m_exists[e];
}

void Registry::add_transform(Entity e, const Transform& t) { ensure(e); m_t[e] = t; }
void Registry::add_velocity (Entity e, const Velocity& v)  { ensure(e); m_v[e] = v; }
void Registry::add_mass     (Entity e, const Mass& m)      { ensure(e); m_m[e] = m; }
void Registry::add_force    (Entity e, const Force& f)     { ensure(e); m_f[e] = f; }
void Registry::add_sphere   (Entity e, const Sphere& s)    { ensure(e); m_spheres[e] = s; m_has_sphere[e] = true; }
void Registry::add_aabb     (Entity e, const AABB& a)      { ensure(e); m_aabbs[e] = a; m_has_aabb[e] = true; }

Transform& Registry::transform(Entity e) { assert(has_alive(e)); return m_t[e]; }
Velocity&  Registry::velocity (Entity e) { assert(has_alive(e)); return m_v[e]; }
Mass&      Registry::mass     (Entity e) { assert(has_alive(e)); return m_m[e]; }
Force&     Registry::force    (Entity e) { assert(has_alive(e)); return m_f[e]; }

const Transform& Registry::transform(Entity e) const { assert(has_alive(e)); return m_t[e]; }
const Velocity&  Registry::velocity (Entity e) const { assert(has_alive(e)); return m_v[e]; }
const Mass&      Registry::mass     (Entity e) const { assert(has_alive(e)); return m_m[e]; }
const Force&     Registry::force    (Entity e) const { assert(has_alive(e)); return m_f[e]; }

bool Registry::has_sphere(Entity e) const { return e < m_has_sphere.size() && m_has_sphere[e]; }
bool Registry::has_aabb(Entity e) const { return e < m_has_aabb.size() && m_has_aabb[e]; }

Sphere& Registry::sphere(Entity e) { assert(has_sphere(e)); return m_spheres[e]; }
AABB& Registry::aabb(Entity e) { assert(has_aabb(e)); return m_aabbs[e]; }

const Sphere& Registry::sphere(Entity e) const { assert(has_sphere(e)); return m_spheres[e]; }
const AABB& Registry::aabb(Entity e) const { assert(has_aabb(e)); return m_aabbs[e]; }

} // namespace ne