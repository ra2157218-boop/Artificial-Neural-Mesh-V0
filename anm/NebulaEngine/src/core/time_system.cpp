#include "time_system.h"
#include <algorithm>

namespace ne {

TimeSystem::TimeSystem(double fixed_dt) : m_fixed_dt(fixed_dt) {}

int TimeSystem::update(double real_dt, int max_steps) {
    if (real_dt < 0.0) real_dt = 0.0;
    // clamp huge pauses (tab switch, debugger pause)
    if (real_dt > 0.25) real_dt = 0.25;

    m_accum += real_dt;

    int steps = 0;
    while (m_accum >= m_fixed_dt && steps < max_steps) {
        m_accum -= m_fixed_dt;
        ++steps;
    }
    return steps;
}

} // namespace ne