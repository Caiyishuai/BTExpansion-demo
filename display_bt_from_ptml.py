from graphviz import Digraph


# 定义一个简单的树节点类
class TreeNode:
    def __init__(self, name):
        self.name = name
        self.children = []

    def add_child(self, child):
        self.children.append(child)


# 手动解析 .ptml 文件
def parse_ptml(file_content):
    lines = file_content.strip().split('\n')
    root = TreeNode('root')
    current_node = root
    stack = [root]

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue

        # 检测缩进级别
        indent = len(line) - len(stripped_line)
        if stripped_line.startswith('selector') or stripped_line.startswith('sequence'):
            # 创建新节点
            new_node = TreeNode(stripped_line.replace('selector{', '?').replace('sequence{', '→'))
            if current_node:
                current_node.add_child(new_node)
                stack.append(new_node)
                current_node = new_node
        elif stripped_line.startswith('cond') or stripped_line.startswith('act'):
            # 创建新节点
            new_node = TreeNode(stripped_line)
            if current_node:
                current_node.add_child(new_node)
        elif stripped_line.startswith('}'):
            # 缩进级别减少，返回上一级
            stack.pop()
            current_node = stack[-1] if stack else root

    return root


# 将树转换为Graphviz可识别的格式，但跳过root节点
def build_graph(node, graph, is_root=False):
    if is_root:  # 如果是root节点，则不添加到图中，但遍历其子节点
        for child in node.children:
            build_graph(child, graph, False)
    else:
        node_id = str(id(node))
        graph.node(node_id, node.name)

        # 设置节点颜色
        if node.name.startswith('cond'):
            graph.node(node_id, node.name, fillcolor='yellow', style='filled')
        elif node.name.startswith('act'):
            graph.node(node_id, node.name, fillcolor='green', style='filled')

        for child in node.children:
            child_id = str(id(child))
            graph.edge(node_id, child_id)
            build_graph(child, graph, False)


# 读取文件内容
with open("MoveBtoB.ptml", "r") as file:
    file_content = file.read()

# 解析文件内容
root = parse_ptml(file_content)

# 创建图
dot = Digraph(comment='PFML Tree without root')

# 从root的直接子节点开始构建图（将is_root设置为True）
if root.children:
    for child in root.children:
        build_graph(child, dot, False)  # 注意这里is_root为False，因为我们是从子节点开始的
else:
    # 如果没有子节点，则图可能为空或仅包含root（此时应决定如何处理）
    print("The root node has no children to display.")

# 保存和查看图（这部分代码未修改）
dot.render('ptml_tree', view=True)