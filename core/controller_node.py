class ControllerNode:
    def __init__(self, name, parent: "ControllerNode" = None):
        self.name = name
        self.parent = parent
        self.children = []
        # self.metadata = {}   # anything you want: size, color, tags, etc.
        self.depth = parent.depth + 1 if parent else 0
        """
        TODO: Scaling controllers based on hierarchy depth
            Your controller_ratio logic is fine.

            One improvement:
                Store ratio as metadata on ControllerNode
            Do not recompute from depth every time
            This will matter if hierarchy changes dynamically.
        """

    def __str__2(self):
        return f"ControllerNode(name = {self.name})"

    def __repr__2(self):
        return f"ControllerNode(name = {self.name})"

    def __str__(self):
        return f"ControllerNode(name = {self.name}, parent = {self.parent}, children = {self.children})"

    def __repr__(self):
        return f"ControllerNode(name = {self.name}, parent = {self.parent}, children = {self.children})"

    def add_child(self, child):
        if not isinstance(child, ControllerNode):
            raise TypeError(f"Child must be ControllerNode, got {type(child)}")
        child.parent = self
        self.children.append(child)
