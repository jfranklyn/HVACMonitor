            client.on_message = on_message
            
        except Exception as e:
            logger.error('Could not connect to MQTT Server {}{}'.format(type(e)$
            
        # check the status of each sensor andreturn the value to the aio dashbo$
        client.publish(localTopic, "RPI 4b Broker Online")
        
        time.sleep(LOOP_INTERVAL)
        client.loop_forever()


if __name__ == "__main__":
    main()    




