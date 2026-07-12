import socket, array, os

path = "/run/paperwork/mgmt.sock"
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect(path)

msg, ancdata, flags, addr = s.recvmsg(4096, socket.CMSG_SPACE(2 * 4))
print("Message:", msg)

fds = array.array("i")
for cmsg_level, cmsg_type, cmsg_data in ancdata:
    if cmsg_level == socket.SOL_SOCKET and cmsg_type == socket.SCM_RIGHTS:
        fds.frombytes(cmsg_data[:len(cmsg_data) - (len(cmsg_data) % fds.itemsize)])

print("Received FDs:", list(fds))

log_fd, admin_fd = fds
data = os.pread(admin_fd, 1024, 0)
print("admin_pins.conf contents:", data.decode(errors="ignore"))
