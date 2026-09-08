# -*- coding: utf-8 -*-
import sys
import time
from pathlib import Path

tools_dir = Path("/Users/cc/Desktop/GGBOM/xxxx/Tools")
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

import official_remote_execution as ore

def test():
    remote = ore.RemoteExecution()
    remote.start()
    found = None
    for _ in range(15):
        if remote.remote_nodes:
            found = remote.remote_nodes[0]
            break
        time.sleep(0.2)

    if found:
        print(f"FOUND_NODE: {found['node_id']} {found['user']}")
        remote.open_command_connection(found['node_id'])
        res = remote.run_command('import unreal; print("HELLO_FROM_UE_MEMORY:", unreal.SystemLibrary.get_engine_version())', exec_mode=ore.MODE_EXEC_STATEMENT)
        print("COMMAND_RESULT:", res)
        remote.close_command_connection()
    else:
        print("NO_NODE_FOUND")
    remote.stop()

if __name__ == "__main__":
    test()
