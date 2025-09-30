# output_manager.py

import queue
import threading
from colorama import Fore, Style


class OutputManager:
    """Manages various output devices by processing commands from a shared queue."""

    def __init__(self, command_queue):
        self.command_queue = command_queue
        self.controllers = {}
        self.threads = {}
        self.running = False

    def add_controller(self, device_type, controller_instance):
        """Adds a new output device controller to the manager."""
        self.controllers[device_type] = controller_instance

    def start(self):
        """Starts the main worker thread and all registered controllers."""
        if not self.running:
            print("OutputManager started.")
            self.running = True
            
            # Start all registered controllers
            for controller in self.controllers.values():
                if hasattr(controller, 'start'):
                    controller.start()

            # The main thread of the OutputManager will process the queue
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            
    def stop(self):
        """Stops the output manager and all its controllers."""
        self.running = False
        print(f"{Fore.RED}OutputManager stopping...{Style.RESET_ALL}")
        for controller in self.controllers.values():
            if hasattr(controller, 'stop'):
                controller.stop()

    # output_manager.py

    def _worker_loop(self):
        """The main loop that waits for and executes commands."""
        while self.running:
            try:
                device_type, params = self.command_queue.get(timeout=0.1)
                
                # --- DEBUG ---
                print(f"{Fore.MAGENTA}--- OutputManager: Dequeued command for '{device_type}' ---{Style.RESET_ALL}")
                # --- END DEBUG ---

                if device_type in self.controllers:
                    controller = self.controllers[device_type]
                    
                    if hasattr(controller, 'set_effect'):
                        controller.set_effect(**params)
                    else:
                        print(f"{Fore.YELLOW}Warning: Controller for '{device_type}' has no 'set_effect' method.{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}Warning: No controller found for device type '{device_type}'.{Style.RESET_ALL}")
                
                self.command_queue.task_done()
                
            except queue.Empty:
                pass
            except Exception as e:
                print(f"{Fore.RED}An error occurred in the OutputManager worker: {e}{Style.RESET_ALL}")
                
    # def _worker_loop(self):
    #     """The main loop that waits for and executes commands."""
    #     while self.running:
    #         try:
    #             device_type, params = self.command_queue.get(timeout=0.1)
                
    #             if device_type in self.controllers:
    #                 controller = self.controllers[device_type]
                    
    #                 if hasattr(controller, 'set_effect'):
    #                     print(f"{Style.DIM}OutputManager: Sending command to {device_type} with params {params}{Style.RESET_ALL}")
    #                     controller.set_effect(**params)
    #                 else:
    #                     print(f"{Fore.YELLOW}Warning: Controller for '{device_type}' has no 'set_effect' method.{Style.RESET_ALL}")
    #             else:
    #                 print(f"{Fore.YELLOW}Warning: No controller found for device type '{device_type}'.{Style.RESET_ALL}")
                
    #             self.command_queue.task_done()
                
    #         except queue.Empty:
    #             pass
    #         except Exception as e:
    #             print(f"{Fore.RED}An error occurred in the OutputManager worker: {e}{Style.RESET_ALL}")