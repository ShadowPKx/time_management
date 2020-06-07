//
//  echolalia.js
//
//  Created by Christian Swinehart on 2010-12-15.
//  Copyright (c) 2011 Samizdat Drafting Co. All rights reserved.
//

var graph = {};
(function($) {

    SimpleRenderer = function(canvas) {
        var canvas = $(canvas).get(0)
        var ctx = canvas.getContext("2d");
        var gfx = arbor.Graphics(canvas);
        var particleSystem = null;

        var that = {
            //
            // the particle system will call the init function once, right before the
            // first frame is to be drawn. it's a good place to set up the canvas and
            // to pass the canvas size to the particle system
            //
            init: function(system) {
                particleSystem = system
                particleSystem.screenSize(canvas.width, canvas.height)
                particleSystem.screenPadding(80) // leave an extra 80px of whitespace per side
                that.initMouseHandling()
            },

            //
            // redraw will be called repeatedly during the run whenever the node positions
            // change. the new positions for the nodes can be accessed by looking at the
            // .p attribute of a given node. however the p.x & p.y values are in the coordinates
            // of the particle system rather than the screen. you can either map them to
            // the screen yourself, or use the convenience iterators .eachNode (and .eachEdge)
            // which allow you to step through the actual node objects but also pass an
            // x,y point in the screen's coordinate system
            //

            redraw: function() {
                if (!particleSystem) return

                gfx.clear() // convenience ƒ: clears the whole canvas rect
                //ctx.clearRect(0, 0, canvas.width, canvas.height)


                var nodeBoxes = {}
                particleSystem.eachNode(function(node, pt) {
                    // node: {mass:#, p:{x,y}, name:"", data:{}}
                    // pt:   {x:#, y:#}  node position in screen coords

                    // draw a rectangle centered at pt
                    /*var w = 10
                    ctx.fillStyle = "black"
                    ctx.fillRect(pt.x - w / 2, pt.y - w / 2, w, w)*/
                    var label = node.data.name || ""
                    var fname = node.data.user || ""
                    var h = 22;
                    var w = ctx.measureText("" + label).width + 12;
                    var w2 = 0;
                    if (!node.data.own) {
                        var w2 = ctx.measureText("" + fname).width + 10
                        if (w2 > w) {
                            w = w2
                        }
                        h = 44
                    }

                    if (!("" + label).match(/^[ \t]*$/)) {
                        pt.x = Math.floor(pt.x)
                        pt.y = Math.floor(pt.y)
                    } else {
                        label = null
                    }

                    // draw a rectangle centered at pt
                    if (node.data.own) {
                        ctx.fillStyle = "#193"
                        if (node.data.selected) {
                            ctx.fillStyle = "#931"
                        }
                    } else {
                        ctx.fillStyle = "#47b"
                        if (node.data.selected) {
                            ctx.fillStyle = "#871"
                        }
                    }

                    gfx.rect(pt.x - w / 2, pt.y - (h / 2) + 1, w, h - 2, 4, {
                        fill: ctx.fillStyle
                    })
                    nodeBoxes[node.name] = [pt.x - w / 2, pt.y - h / 2, w, h]

                    // draw the text
                    if (label) {
                        ctx.font = "14px Helvetica"
                        ctx.textAlign = "center"
                        ctx.fillStyle = "#fff"

                        if (!node.data.own) {
                            ctx.fillText(label || "-", pt.x, pt.y + 4 + h / 4)
                            ctx.fillText(label || "-", pt.x, pt.y + 4 + h / 4)
                            ctx.font = "12px Helvetica"
                            ctx.fillText(fname || "-", pt.x, pt.y + 4 - h / 4)
                        } else {
                            ctx.fillText(label || "-", pt.x, pt.y + 4)
                            ctx.fillText(label || "-", pt.x, pt.y + 4)
                        }
                    }
                });

                particleSystem.eachEdge(function(edge, pt1, pt2) {
                    // edge: {source:Node, target:Node, length:#, data:{}}
                    // pt1:  {x:#, y:#}  source position in screen coords
                    // pt2:  {x:#, y:#}  target position in screen coords

                    // draw a line from pt1 to pt2
                    /*ctx.strokeStyle = "rgba(0,0,0, .5)"
                    ctx.lineWidth = 2
                    ctx.beginPath()
                    ctx.moveTo(pt1.x, pt1.y)
                    ctx.lineTo(pt2.x, pt2.y)
                    ctx.stroke()*/


                    // edge: {source:Node, target:Node, length:#, data:{}}
                    // pt1:  {x:#, y:#}  source position in screen coords
                    // pt2:  {x:#, y:#}  target position in screen coords

                    var weight = edge.data.weight
                    var color = edge.data.color

                    if (!color || ("" + color).match(/^[ \t]*$/)) color = null

                    // find the start point
                    var tail = intersect_line_box(pt1, pt2, nodeBoxes[edge.source.name])
                    var head = intersect_line_box(tail, pt2, nodeBoxes[edge.target.name])

                    ctx.save()
                    ctx.beginPath()
                    ctx.lineWidth = 2
                    //ctx.strokeStyle = (color) ? color : "#cccccc"
                    ctx.strokeStyle = "rgba(0,0,0, .5)"
                    ctx.fillStyle = null

                    ctx.moveTo(tail.x, tail.y)
                    ctx.lineTo(head.x, head.y)
                    ctx.stroke()
                    ctx.restore()

                    // draw an arrowhead if this is a -> style edge

                    ctx.save()
                    // move to the head position of the edge we just drew
                    var wt = !isNaN(weight) ? parseFloat(weight) : 1
                    var arrowLength = 12 + wt
                    var arrowWidth = 5 + wt
                    ctx.fillStyle = "rgba(0,0,0, .7)"
                    ctx.translate(head.x, head.y);
                    ctx.rotate(Math.atan2(head.y - tail.y, head.x - tail.x));

                    // delete some of the edge that's already there (so the point isn't hidden)
                    ctx.clearRect(-arrowLength / 2, -wt / 2, arrowLength / 2, wt)

                    // draw the chevron
                    ctx.beginPath();
                    ctx.moveTo(-arrowLength, arrowWidth);
                    ctx.lineTo(0, 0);
                    ctx.lineTo(-arrowLength, -arrowWidth);
                    ctx.lineTo(-arrowLength * 0.8, -0);
                    ctx.closePath();
                    ctx.fill();
                    ctx.restore()



                })

            },
            initMouseHandling: function() {
                // no-nonsense drag and drop (thanks springy.js)
                selected = null;
                nearest = null;
                var dragged = null;
                var oldmass = 1

                // set up a handler object that will initially listen for mousedowns then
                // for moves and mouseups while dragging
                var handler = {
                    clicked: function(e) {
                        var pos = $(canvas).offset();
                        _mouseP = arbor.Point(e.pageX - pos.left, e.pageY - pos.top)
                        selected = nearest = dragged = particleSystem.nearest(_mouseP);

                        if (dragged.node !== null) dragged.node.fixed = true

                        $(canvas).bind('mousemove', handler.dragged)
                        $(window).bind('mouseup', handler.dropped)
                        $(canvas).bind('touchmove', handler.dragged)
                        $(window).bind('touchend', handler.dropped)

                        return false
                    },
                    dragged: function(e) {
                        var old_nearest = nearest && nearest.node._id
                        var pos = $(canvas).offset();
                        var s = arbor.Point(e.pageX - pos.left, e.pageY - pos.top)

                        if (!nearest) return
                        if (dragged !== null && dragged.node !== null) {
                            var p = particleSystem.fromScreen(s)
                            dragged.node.p = p
                        }

                        return false
                    },

                    dropped: function(e) {
                        if (dragged === null || dragged.node === undefined) return
                        if (dragged.node !== null) dragged.node.fixed = false
                        dragged.node.tempMass = 1000
                        dragged = null
                        selected = null
                        $(canvas).unbind('mousemove', handler.dragged)
                        $(window).unbind('mouseup', handler.dropped)
                        $(canvas).unbind('touchmove', handler.dragged)
                        $(window).unbind('touchend', handler.dropped)

                        _mouseP = null
                        initMoving();
                        return false
                    }
                }
                $(canvas).bind('mousedown', handler.clicked);
                //$(canvas).bind('touchstart', handler.clicked);

            },

        } //var "that" ended


        // helpers for figuring out where to draw arrows (thanks springy.js)
        var intersect_line_line = function(p1, p2, p3, p4) {
            var denom = ((p4.y - p3.y) * (p2.x - p1.x) - (p4.x - p3.x) * (p2.y - p1.y));
            if (denom === 0) return false // lines are parallel
            var ua = ((p4.x - p3.x) * (p1.y - p3.y) - (p4.y - p3.y) * (p1.x - p3.x)) / denom;
            var ub = ((p2.x - p1.x) * (p1.y - p3.y) - (p2.y - p1.y) * (p1.x - p3.x)) / denom;

            if (ua < 0 || ua > 1 || ub < 0 || ub > 1) return false
            return arbor.Point(p1.x + ua * (p2.x - p1.x), p1.y + ua * (p2.y - p1.y));
        }

        var intersect_line_box = function(p1, p2, boxTuple) {
            var p3 = {
                    x: boxTuple[0],
                    y: boxTuple[1]
                },
                w = boxTuple[2],
                h = boxTuple[3]

            var tl = {
                x: p3.x,
                y: p3.y
            };
            var tr = {
                x: p3.x + w,
                y: p3.y
            };
            var bl = {
                x: p3.x,
                y: p3.y + h
            };
            var br = {
                x: p3.x + w,
                y: p3.y + h
            };

            return intersect_line_line(p1, p2, tl, tr) ||
                intersect_line_line(p1, p2, tr, br) ||
                intersect_line_line(p1, p2, br, bl) ||
                intersect_line_line(p1, p2, bl, tl) ||
                false
        }
        return that
    } //class SimpleRenderer ended



    var sys
    graph.init = function(data) {
        sys = arbor.ParticleSystem(1000, 600, 0.5, true, 40, 0.01, 0.5)
        sys.renderer = SimpleRenderer("#viewport") // our newly created renderer will have its .init() method called shortly by sys...
        initMoving();
        sys.graft({
            nodes: data.nodes,
            edges: data.edges
        })

    }


    var stoptimer;

    function initMoving() {
        if (stoptimer) clearTimeout(stoptimer);
        sys.parameters({
            dt: 0.01
        });
        sys.fps(40);
        stoptimer = setTimeout(function() {
            sys.parameters({
                dt: 0.008
            })
            sys.fps(24);
            if (stoptimer) clearTimeout(stoptimer);
            stoptimer = setTimeout(function() {
                sys.stop();
            }, 6000)
        }, 8000);
    }

})(this.jQuery) //module ended

$(document).ready(function() {
    graph.init(response)
})