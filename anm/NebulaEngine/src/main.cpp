#include <iostream>
#include <chrono>
#include <thread>

#include "core/world.h"

int main() {
    ne::Config cfg;
    cfg.restitution = 0.0f;

    ne::World world(cfg);
    world.init_demo();

    auto last = std::chrono::high_resolution_clock::now();

    for (int frame = 0; frame < 600; ++frame) { // 10 seconds at ~60fps input
        auto now = std::chrono::high_resolution_clock::now();
        std::chrono::duration<double> dt = now - last;
        last = now;

        world.tick(dt.count());

        if (frame % 60 == 0) {
            std::cout << "[t=" << (frame/60) << "s] e0.y="
                      << world.registry().transform(1).pos.y
                      << "\n";
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(16));
    }

    return 0;
}