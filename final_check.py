import bolt, time
bolt.bolt.register("test")
with bolt.bolt[0]: time.sleep(0.01)
bolt.bolt.check()
bolt.bolt.stats()
bolt.bolt.top()
