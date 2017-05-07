#!/usr/bin/python
import fcntl, signal, os, time, select
from pysigset import SIGSET, sigemptyset, sigaddset,\
    sigprocmask, SIG_BLOCK, SIG_UNBLOCK
from visage.utils import log

LOG = log.Log()


class ChannelAgent(object):

    def __init__(self, conn_handler, conn_label, dispatcher):

        self.conn_label = conn_label
        self.conn_handler = conn_handler
        self.dispatcher = dispatcher
        self.check_host_connection = False
        self.poller = select.poll()
        self.sigset = SIGSET()
        self._allow_sigio(self.conn_handler)

        self.fd_to_socket = {
            self.conn_handler.fileno(): self.conn_handler
        }

    def _allow_sigio(self, fd):
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_ASYNC)
        fcntl.fcntl(fd, fcntl.F_SETOWN, os.getpid())

    def sigio_handler(self, signal_number, frame):
        if not self.check_host_connection:
            self.mask_sigio()
        self.check_host_connection = True

    def mask_sigio(self):
        sigemptyset(self.sigset)
        sigaddset(self.sigset, signal.SIGIO)
        sigprocmask(SIG_BLOCK, self.sigset, 0);

    def unmask_sigio(self):
        sigemptyset(self.sigset)
        sigaddset(self.sigset, signal.SIGIO)
        sigprocmask(SIG_UNBLOCK, self.sigset, 0);

    def handle_host_msg(self, flag):
        if flag & select.POLLIN:
            data = self.get_request_data()

            # TODO handle IOError data
            # for example, 
            if not data:
                LOG.info("Connection closed")
                self.handle_host_conn_shutdown()
                return
            resp = self.dispatcher(data)
            self.write_back_to_host(resp)

    def get_request_data(self):
        try:
            request_data = self.conn_handler.readline()
            return request_data.strip()
        except IOError as error:
            print error
            pass

    def write_back_to_host(self, resp):
        try:
            if not resp.endswith('\n'):
                self.conn_handler.write(resp)
                self.conn_handler.write('\n')
                self.conn_handler.flush()
            else:
                self.conn_handler.write(resp)
                self.conn_handler.flush()
        except IOError as error:
            print error
            # TODO handle IOError

    def handle_host_conn_shutdown(self):
        self.unmask_sigio()
        self.check_host_connection = False

    def run(self):
        signal.signal(signal.SIGIO, self.sigio_handler)

        while True:

            nfds = 0
            if self.check_host_connection:
                self.poller.register(self.conn_handler, select.POLLIN)
                nfds = nfds + 1

            if nfds > 0:
                try:
                    events = self.poller.poll()
                    for fd, flag in events:
                        s = self.fd_to_socket[fd]
                        if s is self.conn_handler:
                            self.handle_host_msg(flag)

                except select.error as e:
                    print e
            else:
                print "waiting for connection..."
                time.sleep(5)


# if __name__ == '__main__':
#    conn_handler = open("/dev/virtio-ports/org.qemu.guest_agent.1", "r+")
#    ga = ChannelAgent(conn_handler, "test")
#    ga.run()
