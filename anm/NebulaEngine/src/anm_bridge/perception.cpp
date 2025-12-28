#include "perception.h"
#include <sstream>

namespace ne {

std::string Perception::snapshot_text(const Registry& r) {
    std::ostringstream out;
    out << "entities=" << r.alive().size() << "\n";
    for (Entity e : r.alive()) {
        // NOTE: registry accessors are non-const in v0, so this is a stub.
        // We'll upgrade Registry to const-safe in v0.1.
        out << "e=" << e << "\n";
    }
    return out.str();
}

} // namespace ne