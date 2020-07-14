# Implements union-find data structure, augmented with circular linked-list 
# to report members of each union class
class union_find:
    class node:
        def __init__(self, x):
            self.parent = x
            self.next = x
            self.rank = 1
        
        def __str__(self):
            return '{parent: ' + str(self.parent) + ', next: ' + str(self.next) + ', rank: ' + str(self.rank) + '}'
        
    nodes = {}     # union-find nodes
    roots = set()  # set of root notes

    def __str__(self):
        s = '{nodes: ['
        for k, n in self.nodes.items():
            s += ' '
            s += k
            s += ': '
            s += str(n)
        s += '], roots: '
        s += str(self.roots)
        s += '}'
        return s

    # inserts a new node into the union-find forest
    def insert(self, x):
        self.nodes[x] = self.node(x)
        self.roots.add(x)
        # print(self)
        
    # inserts a new node into the union-find tree, only if it isn't already present
    def try_insert(self, x):
        if x in self.nodes:
            return False
        else:
            self.insert(x)
            return True

    # finds the root node for a given element; performs path compression
    def root_node(self, x):
        n = self.nodes[x]
        p = n.parent
        if p == x:
            return n
        r = self.root_node(p)
        n.parent = r.parent
        return r
    
    # finds the root element for a given element
    def root(self, x):
        return self.root_node(x).parent

    # unifies two nodes
    def merge(self, x, y):
        # get roots
        xr = self.root_node(x)
        yr = self.root_node(y)
        # note that root-node parent is that node
        if xr.parent == yr.parent:
            return
        # unify trees
        if xr.rank < yr.rank:
            self.roots.remove(xr.parent)
            xr.parent = yr.parent
        else:
            self.roots.remove(yr.parent)
            yr.parent = xr.parent
            if yr.rank == xr.rank:
                xr.rank += 1
        # merge circularly-linked lists
        t = xr.next
        xr.next = yr.next
        yr.next = t
        # print(self)
    
    # report the members of a given class
    def report(self, x):
        clz = [x]
        n = self.nodes[x].next
        while n != x:
            clz.append(n)
            n = self.nodes[n].next
        return clz
