import glob
import os
from router_util import start_server

# Router 1 info
router_id = "1"
dest_router_1 = "2"
dest_router_2 = "4"
dest_port_1 = 8002
dest_port_2 = 8004
    
# Main Program

# 0. Remove any output files in the output directory
# (this just prevents you from having to manually delete the output files before each run).
files = glob.glob('./output/*')
for f in files:
    os.remove(f)
    
start_server(router_id=router_id, dest_router_1=dest_router_1, dest_port_1=dest_port_1, dest_router_2=dest_router_2, dest_port_2=dest_port_2)
    