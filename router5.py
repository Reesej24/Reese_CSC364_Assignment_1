from router_util import start_server

#global variables for this router
host = "127.0.0.1"
router_id = "5"
router_port = 8005

# Router 5 main()
start_server(router_id=router_id, router_port=router_port)