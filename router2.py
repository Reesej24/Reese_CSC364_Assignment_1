from router_util import start_server

#global variables for this router
host = "127.0.0.1"
router_id = "2"
router_port = 8002
dest_router_1 = 3
dest_router_2 = 4
dest_port_1 = 8003
dest_port_2 = 8004

# Router 2 main()
start_server(router_id=router_id, router_port=router_port, dest_router_1=dest_router_1, dest_port_1=dest_port_1, dest_port_2=dest_port_2)

            
