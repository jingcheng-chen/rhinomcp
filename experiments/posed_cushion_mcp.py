"""Closed-cushion gateway with existing rigid object modification enabled."""

from experiments import layer_modeler_mcp as assembly
from experiments.cushion_body_mcp import mcp

assembly.COMMANDS = assembly.COMMANDS | {"modify_object"}
COMMANDS = assembly.COMMANDS

if __name__ == "__main__":
    mcp.run()
