---
topics:
 - Maya
 - Programming
---
Based on my analysis of your codebase, here are the major refactoring opportunities I identified:

# 1. ControlTreeMayaUI is a God Class (Highest Priority)
ui/control_tree.py is ~936 lines handling too many responsibilities: 
- Tree UI creation/management
- Controller creation logic
 - Animation baking logic
 - Deletion logic
 - Pivot editing coordination
 - Constraint rewiring

Suggested split:
- ControlTreeMayaUI - UI only
- ControllerOperations - Create/delete/bake operations
- AnimationBaker - All baking logic

# 2. Duplicated Baking Logic

Animation baking is scattered across:
- utils/animation.py: copy_anim_from_parent_to_target, copy_anim_from_parent_to_target_smart
- control_tree.py: _bake_with_constraint
- pivot_tools.py: inline baking in __copy_controller_animation

These share similar patterns but have inconsistent options handling.
# 3. Bug: freeze_children has wrong signature

In utils/nodes.py:110:
```python
def freeze_children(self, children: list[str]): # 'self' shouldn't be here
```
This is a standalone function, not a method.

# 4. Mixed UI and Business Logic

 TempControllerWindowMayaUI contains hierarchy traversal logic (__get_tempcontrol_root,  __is_under_tempcontrol) that belongs in utils/hierarchy.py or utils/nodes.py.

# 5. Inconsistent Error Handling
- Some places: cmds.warning()
- Some places: LOGGER.exception() + raise
- Some places: error_dialog() UI popup
- No consistent pattern for user-facing vs internal errors

# 6. PivotTool Callback Complexity
The scriptJob-based selection tracking with __callback, __is_pivot_valid, __pivot_still_selected, __apply_pivot_change chain is hard to follow. Could benefit from a state machine pattern.

# 7. Many Incomplete TODOs

Notable ones:
- controller_node.py:9-16 - Store ratio as metadata
- pivot_tools.py:63-84 - Bake options UI toggle
- control_tree.py:693-696 - Multiple children baking doesn't work
- Relative Space and Camera Space modes are disabled