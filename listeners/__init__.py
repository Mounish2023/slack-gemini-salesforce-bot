from slack_bolt import App

from listeners import actions, assistant, events
from listeners.commands import salesforce_commands


def register_listeners(app: App):
    actions.register(app)
    assistant.register(app)
    events.register(app)
    
    # Register Salesforce commands
    # salesforce_commands.register(app)
