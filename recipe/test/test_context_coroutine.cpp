#include <boost/context/continuation.hpp>
#include <boost/coroutine/asymmetric_coroutine.hpp>
#include <stdexcept>

int main() {
    int value = 0;
    auto context = boost::context::callcc([&](boost::context::continuation&& caller) {
        value = 1;
        caller = caller.resume();
        value = 3;
        return std::move(caller);
    });
    if (value != 1) return 1;
    value = 2;
    context = context.resume();
    if (value != 3 || context) return 2;
    boost::coroutines::asymmetric_coroutine<int>::pull_type sequence(
        [](boost::coroutines::asymmetric_coroutine<int>::push_type& yield) {
            yield(11);
            yield(29);
        });
    if (!sequence || sequence.get() != 11) return 3;
    sequence();
    if (!sequence || sequence.get() != 29) return 4;
    sequence();
    if (sequence) return 5;
    bool unwound = false;
    try {
        boost::context::callcc([&](boost::context::continuation&& caller) {
            try { throw std::runtime_error("context unwind"); }
            catch (const std::runtime_error&) { unwound = true; }
            return std::move(caller);
        });
    } catch (...) { return 6; }
    return unwound ? 0 : 7;
}
