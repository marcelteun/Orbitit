#! /usr/bin/python
#
# Copyright (C) 2010 Marcel Tunnissen
#
# License: GNU Public License version 2
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not,
# check at http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# or write to the Free Software Foundation,
#
#------------------------------------------------------------------

import string
import time

X3D_FMT  = 0
VRML_FMT = 1

class _EMPTY_CLASS_: pass

_INT_TYPE_      = type(1)
_FLOAT_TYPE_    = type(0.1)
_STR_TYPE_      = type('')
_ARR_TYPE_      = type([])
_BOOLEAN_TYPE_  = type(True)
_CLASS_TYPE_    = type(_EMPTY_CLASS_)
_INSTANCE_TYPE_ = type(_EMPTY_CLASS_())

def defAttrs(**dict): return dict

def reindent(str):
    return string.join(string.split(str, '\n'), '\n  ')

def _isDocInstance_(elem):
    return type(elem) == _INSTANCE_TYPE_ and elem.__class__.__name__ == 'Doc'

def _isNodeInstance_(elem):
    return type(elem) == _INSTANCE_TYPE_ and (elem.__class__.__name__ == 'Node' or elem.__class__.__name__ == 'Route')

def _isFloatVecInstance_(elem):
    return type(elem) == _INSTANCE_TYPE_ and elem.__class__.__name__ == 'FloatVec'

def _isIndexInstance_(elem):
    return type(elem) == _INSTANCE_TYPE_ and elem.__class__.__name__ == 'Index'

dbgPrn = True
dbgPrn = False

class Index:
    def __init__(this, indexLst = None):
        this.indexLst = indexLst

    def toVrmlStr(this):
        return this.toX3DStr()

    def toX3DStr(this):
        if dbgPrn: print('Index.toX3DStr:', this.indexLst)
        indexStr = ''
        if this.indexLst != None:
            for i in this.indexLst:
                indexStr = '%s%d ' % (indexStr, i)
        return '%s-1' % indexStr

    # TODO: inherite this from list
    def __len__(this):
        return len(this.indexLst)

    def __getitem__(this, i):
        return this.indexLst[i]

class FloatVec:
    def __init__(this, vec = None, precision = 6):
        this.vec = vec
        this.precision = precision

    def setPrecision(this, p):
        this.precision = p

    def toVrmlStr(this):
        return this.toX3DStr()

    def toX3DStr(this):
        vecStr = ''
        if this.vec != None:
            formatStr = '%%1.%df' % this.precision
            for i in range(len(this.vec)):
                vecCompStr = formatStr % this.vec[i]
                if i == 0:
                    vecStr = vecCompStr
                else:
                    vecStr = '%s %s' % (vecStr, vecCompStr)
        return vecStr

NO_OP = FloatVec([1, 0, 0, 0], 1)

class Node:
    # attrs is a dict
    def __init__(this, thisName, **attrs):
        this.name = thisName
        this.setAttrs(attrs)
        this.format = X3D_FMT

    def addNode(this, node, attrName = ''):
        if attrName == '':
            attrName = node.name
        this.addAttr(attrName, node)
        return this

    def setAttrs(this, attrs):
        this.attrs = attrs

    def addAttr(this, name, value):
        this.attrs[name] = value

    def routeToVrmlStr(this):
        return 'ROUTE %s.%s TO %s.%s' % (
            this.attrs['fromNode'],
            this.attrs['fromField'],
            this.attrs['toNode'],
            this.attrs['toField']
        )

    def valueToVrmlStr(this, val):
        if type(val) == _STR_TYPE_:
            return '"%s"' % val
        if type(val) == _INT_TYPE_:
            return '%d' % val
        if type(val) == _FLOAT_TYPE_:
            return '%f' % val
        elif type(val) == _BOOLEAN_TYPE_:
            if val:
                return 'TRUE'
            else:
                return 'FALSE'
        elif type(val) == _ARR_TYPE_:
            return '[%s\n]' % reindent(this.arrToVrmlStr(val))
        elif _isIndexInstance_(val):
            return '%s' % val.toVrmlStr()
        elif _isFloatVecInstance_(val):
            return '%s' % val.toVrmlStr()
        elif _isNodeInstance_(val):
            if val.name == 'IS':
                assert 'children' in val.attrs
                for node in val.attrs['children']:
                    assert _isNodeInstance_(node)
                    assert node.name == 'connect'
                    assert 'nodeField' in node.attrs
                    assert 'protoField' in node.attrs
                    nodeField  = node.attrs['nodeField']
                    protoField = node.attrs['protoField']
                    assert type(nodeField)  == _STR_TYPE_
                    assert type(protoField) == _STR_TYPE_
                    return '%s IS %s' % (nodeField, protoField)
            else:
                return '%s' % val.toVrmlStr()

    def attrToVrmlStr(this, attrs):
        attrStr = ''
        for attrName, attrValue in attrs.items():
            # string attr values need to be quoted
            if attrName != 'USE' and attrName != 'DEF':
                if attrName == 'IS':
                    attrStr = '%s\n%s' % (attrStr, this.valueToVrmlStr(attrValue))
                else:
                    attrStr = '%s\n%s %s' % (attrStr, attrName, this.valueToVrmlStr(attrValue))
        return attrStr

    def arrToVrmlStr(this, arr):
        arrStr = ''
        for i in range(len(arr)):
            arrValue = arr[i]
            if _isFloatVecInstance_(arrValue) and i != 0:
                arrStr = '%s,\n' % arrStr
            else:
                arrStr = '%s\n' % arrStr
            arrStr = '%s%s' % (arrStr, this.valueToVrmlStr(arrValue))
            if dbgPrn: print('Node.arrToVrmlStr:', arrStr)
        return arrStr

    def toVrmlStr(this):
        if 'USE' in this.attrs:
            return '\nUSE %s' % this.attrs['USE']
        else:
            nodeStr = ''
            if 'DEF' in this.attrs:
                nodeStr = 'DEF %s ' % this.attrs['DEF']
            if this.name == 'ROUTE':
                nodeStr = '%s%s' % (nodeStr, this.routeToVrmlStr())
            elif this.name == 'ProtoDeclare':
                assert 'name' in this.attrs
                nodeStr = '%sPROTO %s ' % (nodeStr, this.attrs['name'])
                #nodeStr = '%sPROTO %s {%s\n}' % (nodeStr, this.attrs['name'], reindent(this.attrToVrmlStr(this.attrs)))
                assert 'children' in this.attrs
                for node in this.attrs['children']:
                    assert _isNodeInstance_(node)
                    nodeStr = '%s%s' % (nodeStr, node.toVrmlStr())
            elif this.name == 'ProtoInterface':
                nodeStr = '%s[' % nodeStr
                assert 'children' in this.attrs
                for node in this.attrs['children']:
                    assert _isNodeInstance_(node)
                    assert node.name in ['field', 'exposedField', 'eventIn', 'eventOut']
                    assert 'type' in node.attrs
                    nodeStr = '%s\n  %s %s' % (nodeStr, node.name, node.attrs['type'])
                    assert 'name' in node.attrs
                    nodeStr = '%s %s' % (nodeStr, node.attrs['name'])
                    assert 'value' in node.attrs
                    nodeStr = '%s %s' % (nodeStr, this.valueToVrmlStr(node.attrs['value']))
                nodeStr = '%s\n]' % nodeStr
            elif this.name == 'ProtoBody':
                nodeStr = '%s\n{' % nodeStr
                assert 'children' in this.attrs
                for node in this.attrs['children']:
                    assert _isNodeInstance_(node)
                    nodeStr = '%s\n  %s' % (nodeStr, reindent(node.toVrmlStr()))
                nodeStr = '%s\n}' % nodeStr
            elif this.name == 'ProtoInstance':
                assert 'name' in this.attrs
                nodeStr = '%s%s {' % (nodeStr, this.attrs['name'])
                assert 'children' in this.attrs
                for node in this.attrs['children']:
                    assert _isNodeInstance_(node)
                    assert node.name == 'fieldValue'
                    assert 'name' in node.attrs
                    nodeStr = '%s\n  %s' % (nodeStr, node.attrs['name'])
                    assert 'value' in node.attrs
                    nodeStr = '%s %s' % (nodeStr, this.valueToVrmlStr(node.attrs['value']))
                nodeStr = '%s\n}' % nodeStr
            else:
                nodeStr = '%s%s {%s\n}' % (nodeStr, this.name, reindent(this.attrToVrmlStr(this.attrs)))
        return nodeStr

    def arrToX3DStr(this, arr):
        arrStr = ''
        for arrValue in arr:
            if arrStr != '':
                if _isFloatVecInstance_(arrValue):
                    arrStr = '%s, ' % arrStr
                else:
                    arrStr = '%s ' % arrStr
            # string arr values need to be quoted
            if type(arrValue) == _STR_TYPE_:
                arrStr = '%s"%s"' % (arrStr, arrValue)
            if type(arrValue) == _INT_TYPE_:
                arrStr = '%s%d' % (arrStr, arrValue)
            if type(arrValue) == _FLOAT_TYPE_:
                arrStr = '%s%f' % (arrStr, arrValue)
            elif type(arrValue) == _BOOLEAN_TYPE_:
                if arrValue:
                    arrStr = '%strue' % arrStr
                else:
                    arrStr = '%sfalse' % arrStr
            elif _isIndexInstance_(arrValue):
                arrStr = '%s%s' % (arrStr, arrValue.toX3DStr())
            elif _isFloatVecInstance_(arrValue):
                arrStr = '%s%s' % (arrStr, arrValue.toX3DStr())
        return arrStr

    def toX3DStr(this):
        attrStr = ''
        childNodes = []
        for attrName, attrValue in this.attrs.items():
            if not _isNodeInstance_(attrValue) and not (
                type(attrValue) == _ARR_TYPE_ and attrValue != [] and _isNodeInstance_(attrValue[0])
            ):
                if attrStr == '':
                    attrStr = ' '
                else:
                    attrStr = '%s\n%s  ' % (attrStr, ' '.rjust(len(this.name)))
            if type(attrValue) == _STR_TYPE_:
                attrStr = '%s%s="%s"' % (attrStr, attrName, attrValue)
            if type(attrValue) == _INT_TYPE_:
                attrStr = "%s%s='%d'" % (attrStr, attrName, attrValue)
            if type(attrValue) == _FLOAT_TYPE_:
                attrStr = "%s%s='%f'" % (attrStr, attrName, attrValue)
            elif type(attrValue) == _BOOLEAN_TYPE_:
                if attrValue:
                    attrStr = "%s%s='true'" % (attrStr, attrName)
                else:
                    attrStr = "%s%s='false'" % (attrStr, attrName)
            elif type(attrValue) == _ARR_TYPE_:
                if attrValue != []:
                    if _isNodeInstance_(attrValue[0]):
                        for node in attrValue:
                            childNodes.append(node)
                    else:
                        attrStr = "%s%s='%s'" % (attrStr, attrName, this.arrToX3DStr(attrValue))
            elif _isIndexInstance_(attrValue):
                attrStr = "%s%s='%s'" % (attrStr, attrName, attrValue.toX3DStr())
            elif _isFloatVecInstance_(attrValue):
                attrStr = "%s%s='%s'" % (attrStr, attrName, attrValue.toX3DStr())
            elif _isNodeInstance_(attrValue):
                childNodes.append(attrValue)
        if attrStr != '':
            nodeStr = '\n<%s%s' % (this.name, attrStr)
        else:
            nodeStr = '\n<%s' % this.name
        if childNodes == []:
            nodeStr = '%s/>' % nodeStr
        else:
            nodeStr = '%s>' % nodeStr
            for c in childNodes:
                nodeStr = '%s%s' % (nodeStr, reindent(c.toX3DStr()))
            nodeStr = '%s\n</%s>' % (nodeStr, this.name)
        return nodeStr

    def setFormat(this, fmt):
        this.format = fmt

    def toStr(this):
        if this.format == VRML_FMT:
            return this.toVrmlStr()
        else:
            return this.toX3DStr()

    def nodeToX3DStr(this, name):
        nodeStr = ''
        childNodes = []
        for attrName, attrValue in this.attrs.items():
            if attrName == name:
                if type(attrValue) == _STR_TYPE_:
                    nodeStr = '%s="%s"' % (attrName, attrValue)
                elif type(attrValue) == _INT_TYPE_:
                    nodeStr = "%s='%d'" % (attrName, attrValue)
                elif type(attrValue) == _FLOAT_TYPE_:
                    nodeStr = "%s='%f'" % (attrName, attrValue)
                elif type(attrValue) == _BOOLEAN_TYPE_:
                    if attrValue:
                        nodeStr = "%s='true'" % (attrName)
                    else:
                        attrStr = "%s='false'" % (attrName)
                elif type(attrValue) == _ARR_TYPE_:
                    nodeStr = "%s='%s'" % (attrName, this.arrToX3DStr(attrValue))
                    # TODO: here the childnodes should be added as well.
                elif _isIndexInstance_(attrValue):
                    nodeStr = "%s='%s'" % (attrName, attrValue.toX3DStr())
                elif _isFloatVecInstance_(attrValue):
                    nodeStr = "%s='%s'" % (attrName, attrValue.toX3DStr())
            elif type(attrValue) == _ARR_TYPE_:
                if attrValue != []:
                    if _isNodeInstance_(attrValue[0]):
                        for node in attrValue:
                            nodeStr = node.nodeToX3DStr(name)
                            if nodeStr != '':
                                break
            elif _isNodeInstance_(attrValue):
                nodeStr = attrValue.nodeToX3DStr(name)
            if nodeStr != '':
                break
        return nodeStr

class Doc:
    def __init__(this, profile = 'IMMERSIVE'):
        this.contents = []
        this.profile = profile
        this.meta = []
        this.format = X3D_FMT

    def __del__(this):
        for obj in this.contents:
            del obj

    def addMeta(this, **meta):
        if this.meta == []:
            this.meta = meta
        else:
            for name, content in meta.items():
                this.meta[name] = content

    def addStdMeta(this, title, bgColor = FloatVec([0.2, 0.5, 1], 1)):
        this.addMeta(title = title)
        this.addMeta(author = 'Marcel Tuennissen')
        this.addMeta(created = time.strftime('%Y-%m-%d, %H:%M'))
        this.addMeta(generator = 'X3D.py')
        this.addNode(Node('WorldInfo', title = title))
        this.addNode(Node(
            'NavigationInfo',
            type = 'EXAMINE',
            # fixes Cortona center of rotation to (0, 0, 0)
            avatarSize = [0, 0, 0, 0, 0, 0],
            headlight = True
        ))
        this.addNode(Node('Background', skyColor = bgColor))

    def setProfile(this, profile):
        this.profile = profile

    def addNode(this, node):
        this.contents.append(node)
        return this

    def toVrmlStr(this):
        docStr = '#VRML V2.0 utf8'
        for node in this.contents:
            #print node, node.__class__.__name__
            assert _isNodeInstance_(node)
            docStr = '%s\n%s' % (docStr, node.toVrmlStr())
        return docStr

    def toX3DStr(this):
        docStr = '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE X3D PUBLIC "ISO//Web3D//DTD X3D 3.0//EN" "http://www.web3d.org/specifications/x3d-3.0.dtd">'
        head = Node('head')
        if this.meta != []:
            for name, content in this.meta.items():
                head.addNode(Node('meta', name = name, content = content))
        sceneStr = '\n<Scene>'
        for node in this.contents:
            assert _isNodeInstance_(node)
            sceneStr = '%s%s' % (sceneStr, reindent(node.toX3DStr()))
        sceneStr = '%s\n</Scene>' % sceneStr
        docStr = '%s\n<X3D profile="%s"\n     xmlns:xsd=\'http://www.w3.org/2001/XMLSchema-instance\'\n     xsd:noNamespaceSchemaLocation=\'http://www.web3d.org/specifications/x3d-3.0.xsd\'>%s%s\n</X3D>' % (
            docStr,
            this.profile,
            reindent(head.toX3DStr()),
            reindent(sceneStr)
        )
        return docStr

    def nodeToX3DStr(this, name):
        nodeStr = ''
        for node in this.contents:
            nodeStr = node.nodeToX3DStr(name)
            if nodeStr != '':
                break
        return nodeStr

    def setFormat(this, fmt):
        this.format = fmt

    def toStr(this):
        if this.format == VRML_FMT:
            return this.toVrmlStr()
        else:
            return this.toX3DStr()

class Route(Node):
    def __init__(this, fromNode, fromField, toNode, toField):
        Node.__init__(this, 'ROUTE',
            fromNode = fromNode,
            fromField = fromField,
            toNode = toNode,
            toField = toField
        )

if __name__ == '__main__':
    myDoc = Doc()
    myDoc.addNode(Node('WorldInfo', title = '6 Cubes Spinning A4 x I / C2 x I'))
    myDoc.addNode(Node('Background', skyColor = FloatVec([0.2, 0.5, 1], 1)))
    myDoc.addNode(Node('NavigationInfo',headlight = True, type = 'EXAMINE'))
    myDoc.addNode(Node('Viewpoint',
            DEF = 'standard',
            position = FloatVec([0, 0, 5], 0),
            jump = False,
            description = 'standard'
        )
    )
    myDoc.addNode(Node('Viewpoint',
            DEF = 'inside',
            orientation = FloatVec([1, 0, 1, 1.67], 2),
            position = FloatVec([0, 0, 0], 0),
            jump = False,
            description = 'inside'
        )
    )
    unitC = Node('Coordinate', point = [
            FloatVec([-1, -1, -1], 0),
            FloatVec([-1, -1,  1], 0),
            FloatVec([-1,  1, -1], 0),
            FloatVec([-1,  1,  1], 0),
            FloatVec([ 1, -1, -1], 0),
            FloatVec([ 1, -1,  1], 0),
            FloatVec([ 1,  1, -1], 0),
            FloatVec([ 1,  1,  1], 0)
        ])

    faceSet = Node('IndexedFaceSet',
        DEF = 'unitCubeFaces',
        coord = unitC,
        coordIndex = [
            Index([5, 7, 3, 1]),
            Index([5, 4, 6, 7]),
            Index([7, 6, 2, 3]),
            Index([3, 2, 0, 1]),
            Index([1, 0, 4, 5]),
            Index([6, 4, 0, 2])
        ],
        normalPerVertex = False,
        ccw             = False,
        solid           = False,
        creaseAngle     = 0.5
    )
    material = Node('Material',
        diffuseColor = FloatVec([0.2, 0.2, 0.9], 1)
    )
    shape = Node('Shape',
        appearance = Node('Appearance',
            material = Node('Material',
                IS = Node('IS',
                    children = [
                        Node('connect',
                            nodeField = 'diffuseColor',
                            protoField = 'cubeColor'
                        )
                    ]
                )
            )
        ),
        geometry = faceSet
    )
    myDoc.addNode(Node('ProtoDeclare',
        name = 'Cube',
        children = [
            Node('ProtoInterface',
                children = [
                    Node('field',
                        type  = 'SFColor',
                        name  = 'cubeColor',
                        value = FloatVec([0.2, 0.3, 0.9]),
                        accessType = 'initializeOnly'
                    )
                ]
            ),
            Node('ProtoBody', children = [shape])
        ]
    ))
    # After the protoype declartion the rest may follow:
    transform = Node('Transform',
        children = [
            Node('ProtoInstance',
                name = 'Cube',
                children = [
                    Node('fieldValue', name = 'cubeColor', value = FloatVec([0.2, 0.2, 0.9], 1))
                ]
            ),
            Node('TouchSensor', DEF = 'ts')
        ]
    )
    myDoc.addNode(transform)
    myDoc.addNode(Node('ROUTE',
        fromNode = 'ts',
        fromField = 'isActive',
        toNode = 'inside',
        toField = 'set_bind'
    ))
    #myDoc.addMeta(filename = 'blablabl')
    file = open('tst.x3d.wrl', 'w')
    file.write(myDoc.toVrmlStr())
    file.close
    file = open('tst.x3d.x3d', 'w')
    file.write(myDoc.toStr())
    file.close
