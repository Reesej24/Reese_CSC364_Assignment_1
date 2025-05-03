from router_util import start_server

#global variables for this router
host = "127.0.0.1"
router_id = "4"
router_port = 8004
dest_router_1 = 5
dest_router_2 = 6
dest_port_1 = 8005
dest_port_2 = 8006

# Router 4 main()

start_server(router_id=router_id, router_port=router_port, dest_router_1=dest_router_1, dest_port_1=dest_port_1, dest_port_2=dest_port_2)