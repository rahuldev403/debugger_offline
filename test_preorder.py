class Node: 
    def __init__(self, val): 
        self.val = val 
        self.left = None 
        self.right = None 

def preorder(root, res): 
    if not root: 
        return 
    
    # Preorder: Visit root FIRST, then left, then right
    res.append(root.val)  # This must come FIRST for preorder
    preorder(root.left, res) 
    preorder(root.right, res) 

root = Node(1) 
root.left = Node(2) 
root.right = Node(3) 

res = [] 
preorder(root, res) 
print(res)  # Should output: [1, 2, 3]

