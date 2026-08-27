from dataclasses import dataclass, field


@dataclass
class AgentState:
    max_iterations: int = 10
    iteration: int = 0
    history: list = field(default_factory=list)
    finished: bool = False
    success: bool = False
    summary: str = ""

    def record(self, action: str, args: dict, reasoning: str, observation: str):
        self.history.append(
            {
                "iteration": self.iteration,
                "action": action,
                "args": args,
                "reasoning": reasoning,
                "observation": observation,
            }
        )

    def called(self, action_name: str, success_marker: str) -> bool:
        return any(
            h["action"] == action_name and success_marker in h["observation"]
            for h in self.history
        )

    def history_as_text(self) -> str:
        if not self.history:
            return "(nothing yet)"
        lines = []
        for h in self.history:
            lines.append(
                f"[{h['iteration']}] action={h['action']} args={h['args']} "
                f"reasoning=\"{h['reasoning']}\"\n    observation: {h['observation'][:600]}"
            )
        return "\n".join(lines)
