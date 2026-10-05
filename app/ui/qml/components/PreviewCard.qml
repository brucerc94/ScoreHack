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
                          ? "Reconstrucción de partitura"
                          : "Vista previa del frame"
                    color: "#f4f7fb"
                    font.pixelSize: 17
                    font.bold: true
                }

                Label {
                    text: backend.layoutMode === "horizontal"
                          ? "Selecciona frames y controla cada unión"
                          : "Ajusta el recorte y el rango antes de exportar"
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
                      : "Sin video"
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
                    text: "Analiza un video para comenzar"
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
                          ? "Selecciona al menos 2 frames"
                          : "Preparando reconstrucción…"
                    color: "#59677c"
                }
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
                text: "Agregar frame"
                enabled: backend.frameCount > 0
                         && !backend.busy
                         && !backend.currentFrameSelected
                onClicked: backend.toggleCurrentFrameSelection()
            }

            Button {
                Layout.preferredWidth: 90
                Layout.preferredHeight: 36
                text: "Vaciar"
                enabled: backend.selectedFrameCount > 0 && !backend.busy
                onClicked: backend.clearFrameSelection()
            }

            Label {
                Layout.fillWidth: true
                text: backend.selectedFrameCount === 0
                      ? "Elige un frame y pulsa Agregar frame."
                      : "Los frames se unen de izquierda a derecha."
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
                        text: "Solapes por unión"
                        color: "#dbe5f2"
                        font.pixelSize: 12
                        font.bold: true
                    }

                    Item { Layout.fillWidth: true }

                    Label {
                        text: "Cada frame tiene su propio ajuste"
                        color: "#677990"
                        font.pixelSize: 9
                    }
                }

                ListView {
                    id: joinList
                    property real preservedContentY: 0
                    property bool restoringContentY: false

                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 4
                    model: backend.joinItems
                    boundsBehavior: Flickable.StopAtBounds

                    onContentYChanged: {
                        if (!restoringContentY)
                            preservedContentY = contentY
                    }

                    onModelChanged: {
                        restoringContentY = true
                        Qt.callLater(function() {
                            var maximum = Math.max(0, contentHeight - height)
                            contentY = Math.min(preservedContentY, maximum)
                            restoringContentY = false
                        })
                    }

                    delegate: Rectangle {
                        width: joinList.width
                        height: 48
                        radius: 7
                        color: "#111a28"
                        border.color: modelData.manual ? "#315f91" : "#1b2a3f"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 8
                            anchors.rightMargin: 8
                            spacing: 6

                            Label {
                                Layout.preferredWidth: 98
                                text: modelData.label
                                color: "#dbe5f2"
                                font.pixelSize: 10
                                font.bold: true
                                elide: Text.ElideRight
                            }

                            Slider {
                                id: seamSlider
                                Layout.fillWidth: true
                                from: 0
                                to: Math.max(16, Math.round(backend.montageFrameWidth * 0.70))
                                value: modelData.overlap
                                enabled: backend.montageFrameWidth > 0 && !backend.montageBusy
                                onPressedChanged: {
                                    if (!pressed)
                                        backend.setJoinOverlap(modelData.join, value)
                                }
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
                                    text: modelData.manual
                                          ? "Manual"
                                          : (modelData.autoReliable ? "Auto" : "Ajustar")
                                    color: modelData.manual ? "#7aaef2" : "#71839c"
                                    font.pixelSize: 8
                                }
                            }

                            Button {
                                Layout.preferredWidth: 42
                                Layout.preferredHeight: 24
                                text: "Auto"
                                enabled: !backend.montageBusy
                                onClicked: backend.resetJoinOverlap(modelData.join)
                            }
                        }
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }
    }
}
