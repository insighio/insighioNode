import _thread

network_transmit_mutex = _thread.allocate_lock()
