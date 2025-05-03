from router_util import start_server

#global variables for this router
host = "127.0.0.1"
router_id = "3"
router_port = 8003

# Router 3 main()
start_server(router_id=router_id, router_port=router_port)