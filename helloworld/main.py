""""
Then for put/sub, the subscriber calls wait on the outlet, 
and the client calls publish on an entity. 
If the entity has one or multiple matching subscription, 
then the publish gets routed to all outlets there is a subscription to. 

Then the event gets either stored on the outlet until someone calls wait on it. If someone was already waiting an event, then they receive it instantly.
So there's the wait and publish calls. That's a total of 4

-> What happens when we can wait_event , But pull down the connection before we are responded to?.
-> What if we publish to an outlet first way before, we call wait_event, then on calling wait event the connection is cut?.
"""
    
from sys import exit
from dotenv import load_dotenv, find_dotenv
import orchestra.env as env
import avesterra as av
from avesterra import av
from orchestra import mount
from orchestra.orchestra_adapter import OrchestraAdapter, ValueType
from threading import Thread
import time

MOUNT_KEY = "connection_tester"

class ConnectionTester():
    local_entity: av.AvEntity
    local_outlet: av.AvEntity
    auth: av.AvAuthorization
    target: str

    def ping_host(self, host, auth) -> bool:
        try:
            avesterra_model = av.retrieve_avesterra(server=host, authorization=auth)
            print(f"Entity reachable: {host}")
            if avesterra_model:
                return True
            return False
        except Exception as e:
            print(f"Entity not reachable: {e}")
            return False
        
    def on_init(self):
        
        self.local_entity = self.get_or_create_entity(name="connection_test_local_entity", auth=self.auth)
        self.local_outlet = self.get_or_create_outlet(name="connection_test_local_outlet", auth=self.auth)
        av.subscribe_event(self.local_entity, self.local_outlet, authorization=self.auth)
        print(self.local_entity, self.local_outlet)

        time.sleep(1)

        publishing_thread = Thread(target=self.publish)
        publishing_thread.start()

        time.sleep(1)

        waiting_thread = Thread(target=self.wait)
        waiting_thread.start()

        time.sleep(1)

        #av.synchronize_outlet(outlet=av.AvEntity.from_str(self.target), authorization=self.auth)
        #av.flush_events(av.AvEntity.from_str(self.target), authorization=self.auth)


    def adapt(self):
        """
        So for adapt, the adapter calls adapt on the outlet, and the client calls invoke on an entity.
        If the entity has a matching connection to an outlet the invoke calls get routed to the outlet.
        Then if an adapt meets an invoke in the outlet, the adapter receives the call and handles it.
        So there's the adapt and invoke calls, that's two.
        """
        def callback(args: av.InvokeArgs):
            pass
         
        av.adapt_outlet(
            outlet=av.AvEntity.from_str(self.target),
            timeout=av.AvTimeout(100),
            authorization=self.auth,
            callback=callback
        )
    
    def invoker(self):
        target_host = av.AvEntity.from_str(self.target)
   
        host_eid = av.AvEntity(1000, 5002, 0)
        host_payload = {
            "host_eid": av.AvValue.encode_string(str(host_eid)),
        }

        response = av.invoke_entity(
            entity=target_host,
            method=av.AvMethod.TEST,
            attribute=av.AvAttribute.HOST,
            value=av.AvValue.encode_aggregate(host_payload),
            precedence=1,
            authorization=self.auth,
        )

        print(response)

    def invoker_with_retry(self):
        target_host = av.AvEntity.from_str(self.target)
   
        host_eid = av.AvEntity(1000, 1000, 0)
        host_payload = {
            "host_eid": av.AvValue.encode_string(str(host_eid)),
        }
        
        response = av.invoke_entity_retry_bo(
            entity=target_host,
            method=av.AvMethod.TEST,
            attribute=av.AvAttribute.HOST,
            value=av.AvValue.encode_aggregate(host_payload),
            precedence=1,
            authorization=self.auth,
        )

        print(response)

    def wait(self):
        while True:
            print("waiting events")   
            event = av.wait_event(
                outlet=self.local_outlet,
                authorization=self.auth
            )
            print(event)
            time.sleep(2)

    def publish(self):
        for i in range(10):
            av.publish_event(self.local_entity, name=f"event_{i}", authorization=self.auth)
            print("published_event")
    
    def get_or_create_entity(self, name: str, auth: av.AvAuthorization) -> av.AvEntity:
        key = name.replace(" ", "_")
        try:
            return av.registries.lookup_registry(
                registry=av.AvEntity(0, 0, 1), key=key, authorization=auth
            )
        except Exception as e:
            av.av_log.info(f"creating entity: {e}")
            entity = av.avial.create_entity(name, authorization=auth)

            av.registries.deregister_entity(
                registry=av.AvEntity(0, 0, 1),
                key=key,
                authorization=auth,
            )

            # register outlet with <1> registry - The Avesterra registry.
            av.registries.register_entity(
                registry=av.AvEntity(0, 0, 1),
                name=name,
                key=key,
                entity=entity,
                authorization=auth,
            )

            return entity

    def get_or_create_outlet(self, name: str, auth: av.AvAuthorization) -> av.AvEntity:
        """
        Returns the adapter outlet if it already exists. Otherwise, creates adapter outlet.

        Parameters:
        name: The name of the adapter outlet
        auth: The authorization

        Return:
        The adapter outlet
        """
        key = name.replace(" ", "_")
        # First check using the key to see if entity already exists Avesterra registry
        try:

            return av.lookup_registry(
                registry=av.AvEntity(0, 0, 1), key=key, authorization=auth
            )

        except Exception:
            # Create the adapter outlet based on params passed in
            outlet = av.objects.create_object(
                name=name,
                key=key,
                context=av.AvContext.ORCHESTRA,
                klass=av.AvClass.ADAPTER,
                category=av.AvCategory.ADAPTER,
                authorization=auth,
            )

            # Activate the adapter outlet so it can receive attachments or connections
            av.activate_entity(outlet=outlet, authorization=auth)

            # register outlet with <1> registry - The Avesterra registry.
            av.registries.register_entity(
                registry=av.AvEntity(0, 0, 1),
                name=name,
                key=key,
                entity=outlet,
                authorization=auth,
            )

            return outlet


if __name__ == "__main__":

    load_dotenv(find_dotenv())

    adapter = OrchestraAdapter(
        mount_key="connection_tests",
        version="1.0.0",
        description="Connection tester",
        adapting_threads=1,
        socket_count=32,
    )

    connection_tester = ConnectionTester()
    connection_tester.auth = env.get_or_raise(env.AVESTERRA_AUTH, av.AvAuthorization)
    connection_tester.target = "<1000|5002|100141>"

    init_thread = Thread(target=connection_tester.on_init)
    init_thread.start()

    adapter.run()