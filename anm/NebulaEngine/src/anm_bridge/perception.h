#pragma once
#include <string>
#include "../ecs/registry.h"

namespace ne {

// v0: a simple log snapshot (later: structured tensors/events for ANM)
class Perception {
public:
    static std::string snapshot_text(const Registry& r);
};

} // namespace ne