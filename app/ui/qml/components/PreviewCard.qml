import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    Layout.fillWidth: true
    Layout.fillHeight: true
    radius: 16
    color: "#111827"
    border.color: "#1d2a3c"
    clip: true

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 7

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 26

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0

                Label {
                    text: backend.layoutMode === "horizontal"
                          ? "Score reconstruction"
                          : "Frame preview"
                    color: "#f4f7fb"
                    font.pixelSize: 17
                    font.bold: true
                }

                Label {
                    text: backend.layoutMode === "horizontal"
                          ? "Select frames and control each join"
                          : "Adjust crop and frame range before export"
                    color: "#687993"
                    font.pixelSize: 10
                }
            }

            Rectangle {
                visible: backend.layoutMode === "horizontal"
                Layout.preferredWidth: 86
                Layout.preferredHeight: 24
                radius: 8
                color: "#182233"

                Label {
                    anchors.centerIn: parent
                    text: backend.selectedFrameCount + " frames"
                    color: "#9ab0cf"
                    font.pixelSize: 10
                    font.bold: true
                }
            }

            Label {
                text: backend.frameCount > 0
                      ? ("Frame " + (backend.currentFrame + 1) + " / " + backend.frameCount)
                      : "No video"
                color: "#70819a"
                font.pixelSize: 11
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 245
            spacing: 8

            Rectangle {
                Layout.fillWidth: backend.layoutMode === "individual"
                Layout.fillHeight: true
                Layout.preferredWidth: backend.layoutMode === "individual" ? 1 : 260
                radius: 12
                color: "#070b12"
                border.color: "#1b293b"
                clip: true

                Image {
                    id: frameImage
                    anchors.centerIn: parent
                    width: Math.min(parent.width - 18, sourceSize.width)
                    height: Math.min(parent.height - 18, sourceSize.height)
                    source: backend.currentFrameSource
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    cache: false
                }

                Rectangle {
                    visible: backend.frameCount > 0 && backend.cropTop > 0
                    x: frameImage.x
                    y: frameImage.y
                         + backend.cropTop * frameImage.height / Math.max(1, frameImage.sourceSize.height)
                    width: frameImage.width
                    height: 2
                    color: "#25a7ff"
                }

                Rectangle {
                    visible: backend.frameCount > 0 && backend.cropBottom > 0
                    x: frameImage.x
                    y: frameImage.y + frameImage.height
                         - backend.cropBottom * frameImage.height / Math.max(1, frameImage.sourceSize.height)
                    width: frameImage.width
                    height: 2
                    color: "#ff6682"
                }

                Label {
                    anchors.centerIn: parent
                    visible: backend.frameCount === 0
                    text: "Analyze a video to begin"
                    color: "#59677c"
                }
            }

            Rectangle {
                visible: backend.layoutMode === "horizontal"
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 12
                color: "#070b12"
                border.color: "#1b293b"
                clip: true

                Flickable {
                    id: reconstructionView
                    anchors.fill: parent
                    anchors.margins: 6
                    visible: backend.montagePreviewSource !== ""
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    flickableDirection: Flickable.HorizontalFlick
                    contentWidth: reconstructionImage.width + 12
                    contentHeight: height

                    Image {
                        id: reconstructionImage
                        x: 6
                        y: 6
                        height: Math.max(1, reconstructionView.height - 12)
                        width: sourceSize.width > 0
                               ? Math.max(1, sourceSize.width * height / sourceSize.height)
                               : 1
                        source: backend.montagePreviewSource
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        cache: false
                    }

                    Repeater {
                        model: backend.layoutCutCount

                        delegate: Rectangle {
                            id: cutMarker
                            property real sourcePosition: backend.layoutCutPosition(index)

                            x: reconstructionImage.x
                               + sourcePosition * reconstructionImage.width
                               - width / 2
                            y: reconstructionImage.y
                            width: 18
                            height: reconstructionImage.height
                            color: "#ef476f"
                            opacity: 0.82
                            z: 10

                            Rectangle {
                                anchors.horizontalCenter: parent.horizontalCenter
                                anchors.top: parent.top
                                width: 70
                                height: 22
                                radius: 7
                                color: "#ef476f"

                                Label {
                                    anchors.centerIn: parent
                                    text: "Cut " + (index + 1)
                                    color: "white"
                                    font.pixelSize: 9
                                    font.bold: true
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.SizeHorCursor
                                drag.target: cutMarker
                                drag.axis: Drag.XAxis
                                drag.minimumX: reconstructionImage.x - cutMarker.width / 2
                                drag.maximumX: reconstructionImage.x
                                                  + reconstructionImage.width
                                                  - cutMarker.width / 2

                                onReleased: {
                                    var position = (
                                        cutMarker.x
                                        + cutMarker.width / 2
                                        - reconstructionImage.x
                                    ) / Math.max(1, reconstructionImage.width)
                                    backend.setLayoutCut(index, position)
                                }
                            }
                        }
                    }

                    ScrollBar.horizontal: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }
                }

                BusyIndicator {
                    anchors.centerIn: parent
                    visible: backend.montageBusy
                    running: visible
                    width: 28
                    height: 28
                }

                Label {
                    anchors.centerIn: parent
                    visible: !backend.montageBusy && backend.montagePreviewSource === ""
                    text: backend.selectedFrameCount < 2
                          ? "Select at least 2 frames"
                          : "Preparing reconstruction…"
                    color: "#59677c"
                }
            }
        }

        RowLayout {
            visible: backend.layoutMode === "horizontal"
            Layout.fillWidth: true
            Layout.preferredHeight: 38
            spacing: 8

            Label {
                text: "Page cuts: " + backend.layoutCutCount
                color: "#dbe5f2"
                font.pixelSize: 11
                font.bold: true
            }

            Button {
                Layout.preferredWidth: 150
                Layout.preferredHeight: 34
                text: "Add cut here"
                enabled: backend.montagePreviewSource !== "" && !backend.montageBusy
                onClicked: {
                    var center = (
                        reconstructionView.contentX
                        + reconstructionView.width * 0.5
                        - reconstructionImage.x
                    ) / Math.max(1, reconstructionImage.width)
                    backend.addLayoutCut(center)
                }
            }

            Button {
                Layout.preferredWidth: 115
                Layout.preferredHeight: 34
                text: "Clear cuts"
                enabled: backend.layoutCutCount > 0 && !backend.busy
                onClicked: backend.clearLayoutCuts()
            }

            Label {
                Layout.fillWidth: true
                text: "Drag the pink lines to decide where the score is split."
                color: "#77879f"
                font.pixelSize: 10
                elide: Text.ElideRight
            }
        }

        Slider {
            Layout.fillWidth: true
            Layout.preferredHeight: 24
            from: 0
            to: Math.max(1, backend.frameCount - 1)
            value: backend.currentFrame
            enabled: backend.frameCount > 0 && !backend.busy
            onMoved: backend.setFrameIndex(value)
        }

        RowLayout {
            visible: backend.layoutMode === "horizontal"
            Layout.fillWidth: true
            Layout.preferredHeight: 38
            spacing: 8

            Button {
                Layout.preferredWidth: 150
                Layout.preferredHeight: 36
                text: "Add frame"
                enabled: backend.frameCount > 0
                         && !backend.busy
                         && !backend.currentFrameSelected
                onClicked: backend.toggleCurrentFrameSelection()
            }

            Button {
                Layout.preferredWidth: 90
                Layout.preferredHeight: 36
                text: "Clear"
                enabled: backend.selectedFrameCount > 0 && !backend.busy
                onClicked: backend.clearFrameSelection()
            }

            Label {
                Layout.fillWidth: true
                text: backend.selectedFrameCount === 0
                      ? "Choose a frame and click Add frame."
                      : "Frames are joined from left to right."
                color: "#7b8ba3"
                font.pixelSize: 11
                elide: Text.ElideRight
            }
        }

        RowLayout {
            visible: backend.layoutMode === "horizontal"
            Layout.fillWidth: true
            Layout.preferredHeight: 66
            spacing: 8

            Label {
                Layout.preferredWidth: 44
                text: "Frames"
                color: "#8290a6"
                font.pixelSize: 11
                font.bold: true
            }

            ListView {
                id: selectedFrames
                Layout.fillWidth: true
                Layout.fillHeight: true
                orientation: ListView.Horizontal
                spacing: 6
                clip: true
                model: backend.selectedFrameSources
                boundsBehavior: Flickable.StopAtBounds

                delegate: Rectangle {
                    width: 84
                    height: 62
                    radius: 8
                    color: "#0d1522"
                    border.color: "#2b3b53"

                    Image {
                        anchors.fill: parent
                        anchors.margins: 3
                        source: modelData
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        cache: false
                    }

                    Rectangle {
                        anchors.left: parent.left
                        anchors.top: parent.top
                        width: 24
                        height: 19
                        radius: 6
                        color: "#111827"

                        Label {
                            anchors.centerIn: parent
                            text: index + 1
                            color: "#cbd5e3"
                            font.pixelSize: 10
                            font.bold: true
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: backend.removeSelectedFrame(index)
                    }
                }
            }
        }

        Rectangle {
            visible: backend.layoutMode === "horizontal" && backend.joinCount > 0
            Layout.fillWidth: true
            Layout.preferredHeight: 135
            radius: 10
            color: "#0d1522"
            border.color: "#1b2a3f"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 9
                spacing: 5

                RowLayout {
                    Layout.fillWidth: true

                    Label {
                        text: "Joins"
                        color: "#dbe5f2"
                        font.pixelSize: 12
                        font.bold: true
                    }

                    Item { Layout.fillWidth: true }

                    Label {
                        text: "Each join has its own setting"
                        color: "#677990"
                        font.pixelSize: 9
                    }
                }

                ListView {
                    id: joinList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 4
                    model: backend.joinCount
                    boundsBehavior: Flickable.StopAtBounds

                    delegate: Rectangle {
                        width: joinList.width
                        height: 48
                        radius: 7
                        color: "#111a28"
                        border.color: backend.joinIsManual(index)
                                      ? "#315f91"
                                      : "#1b2a3f"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 8
                            anchors.rightMargin: 8
                            spacing: 6

                            Label {
                                Layout.preferredWidth: 98
                                text: backend.joinLabel(index)
                                color: "#dbe5f2"
                                font.pixelSize: 10
                                font.bold: true
                                elide: Text.ElideRight
                            }

                            Slider {
                                id: seamSlider
                                Layout.fillWidth: true
                                from: 0
                                to: Math.max(
                                    16,
                                    Math.round(backend.montageFrameWidth * 0.70)
                                )
                                value: backend.joinOverlap(index)
                                enabled: backend.montageFrameWidth > 0
                                         && !backend.montageBusy
                                onMoved: backend.setJoinOverlap(index, value)
                            }

                            ColumnLayout {
                                Layout.preferredWidth: 72
                                spacing: 0

                                Label {
                                    text: seamSlider.value + " px"
                                    color: "#cbd5e3"
                                    font.pixelSize: 9
                                }

                                Label {
                                    text: backend.joinIsManual(index)
                                          ? "Manual"
                                          : (backend.joinAutoReliable(index)
                                                ? "Auto"
                                                : "Adjust")
                                    color: backend.joinIsManual(index)
                                           ? "#7aaef2"
                                           : "#71839c"
                                    font.pixelSize: 8
                                }
                            }

                            Button {
                                Layout.preferredWidth: 42
                                Layout.preferredHeight: 24
                                text: "Auto"
                                enabled: !backend.montageBusy
                                onClicked: backend.resetJoinOverlap(index)
                            }
                        }
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }
    }
}
