import socket, re
import sys, argparse
import pdb
import json


def send_cmd(cmd, s):
    if isinstance(cmd, str):
        cmd = cmd.encode("ascii")

    s.send(cmd)

    result = bytearray()
    while True:
        data = s.recv(2048)
        if not data:
            break
        result.extend(data)
        # TODO: "\nEND" might be safer?
        # TODO: why is this needed?
        if b"END" in data:
            break
    # TODO: could use walrus instead:
    # while (data := s.recv(2048)):
    #     result.extend(data)
    #     if b"END" in data:
    #         break

    response = result.decode("ascii")
    return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        action="store",
        dest="host",
        default="127.0.0.1",
        help="memcached server host, (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        action="store",
        dest="port",
        type=int,
        default="11211",
        help="memcached server port, (default: 11211)",
    )
    # TODO: dump to stdout by default
    parser.add_argument(
        "--path",
        action="store",
        dest="path",
        default="/tmp/memcached.json",
        help="File path, (default: /tmp/memcached.json)",
    )
    args = parser.parse_args()

    socket.setdefaulttimeout(10)
    pdb.set_trace()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((args.host, args.port))

        items_pack = send_cmd(b"stats items\n", s)
        items = re.findall(r"STAT items:(\d+):number (\d+)", items_pack)

        result = []
        for item_index, item_length in items:
            key_str = send_cmd(f"stats cachedump {item_index} {item_length}\n", s)
            for k, length in re.findall(r"ITEM ([^\s]+) \[(\d+) b", key_str):
                if int(length) == 0:
                    continue
                value = send_cmd(f"get {k}\n", s)
                d = re.search("\\r\\n(?P<value>[^\\s]+)", value).groupdict()
                result.append({"key": k, "len": length, "value": d["value"]})

    with open(args.path, "w") as fp:
        json.dump(result, fp, indent=4, ensure_ascii=False)
