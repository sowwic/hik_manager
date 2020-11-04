import pymel.core as pm
import json
from hik_manager import Logger


class HIKManager:
    def __init__(self, character_node):
        self.character_node = None
        self.properties_node = None
        if character_node:
            self.character_node = pm.PyNode(character_node)

    @staticmethod
    def toggle_lock_definition():
        pm.mel.eval("evalDeferred hikToggleLockDefinition;")

    def export_definition(self, path):
        # Serialize skeleton definition
        self.properties_node = self.character_node.propertyState.listConnections(d=1)[0]  # type: pm.PyNode
        export_data = {}
        definition_data = {}
        properties_data = {}
        for connection in self.character_node.listConnections(c=1, t="joint"):
            definition_data[connection[0].attrName()] = connection[1].name()
        # Serialize HIK properties
        for attr in pm.listAttr(self.properties_node, se=1, o=1):
            properties_data[attr] = pm.getAttr("{0}.{1}".format(self.properties_node, attr))

        export_data["character_name"] = str(self.character_node)
        export_data["definition"] = definition_data
        export_data["properties"] = properties_data
        with open(path, "w") as json_file:
            json.dump(export_data, json_file, indent=4)

        Logger.info("Exported {0} definition to: {1}".format(str(self.character_node), path))

    def import_definition(self, path, lock=True):
        # Create new HIK node if one is not setup
        if not self.character_node:
            self.character_node = pm.createNode("HIKCharacterNode")  # type: pm.PyNode
            self.properties_node = pm.createNode("HIKProperty2State")  # type: pm.PyNode
            self.properties_node.message.connect(self.character_node.propertyState)
        else:
            self.properties_node = self.character_node.propertyState.listConnections(d=1)[0]  # type: pm.PyNode

        definition = {}
        properties = {}
        with open(path, "r") as json_file:
            imported_data = json.load(json_file)
            self.character_node.rename(imported_data["character_name"])
            self.properties_node.rename(imported_data["character_name"] + "_HIKProperties")
            definition = imported_data.get("definition", {})
            properties = imported_data.get("properties", {})

        # Apply definition data
        for attr_name, obj in definition.items():
            obj = pm.PyNode(obj)
            if not pm.hasAttr(obj, "Character"):
                pm.addAttr(obj, ln="Character", at="message")
            obj.Character.connect("{0}.{1}".format(self.character_node, attr_name), f=1)

        # Apply properties data
        for attr, value in properties.items():
            try:
                pm.setAttr("{0}.{1}".format(self.properties_node, attr), value)
            except Exception:
                Logger.exception("Failed to setAttr: {0}, {1}".format(attr, value))

        # Update UI and lock
        pm.mel.eval('hikUpdateContextualUI()')
        if lock:
            HIKManager.toggle_lock_definition()
        Logger.info("Imported HIK definition: {0}".format(path))

    def export_custom_rig(self, path):
        pass

    def import_custom_rig(self, path):
        pass


if __name__ == "__main__":
    character_node = None
    # character_node = pm.ls(sl=1)[-1]  # type: pm.PyNode
    manager = HIKManager(character_node)
    # manager.export_definition("D:/test.json")
    manager.import_definition("D:/test.json")
