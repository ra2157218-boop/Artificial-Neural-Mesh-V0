#pragma once
namespace ne {

class TimeSystem {
public:
    explicit TimeSystem(double fixed_dt = 1.0 / 60.0);

    // Returns how many fixed steps to simulate this tick (0..max_steps)
    int update(double real_dt, int max_steps);

    double fixed_dt() const { return m_fixed_dt; }

private:
    double m_fixed_dt;
    double m_accum = 0.0;
};

} // namespace ne