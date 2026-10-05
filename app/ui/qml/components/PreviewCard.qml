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

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 24

            Label {
                text: backend.layoutMode === "horizontal"
                      ? "Reconstrucción de partitura"
                      : "Vista previa"
                color: "#f4f7fb"
                font.pixelSize: 16
                font.bold: true
            }

            Item { Layout.fillWidth: true }

            Rectangle {
                visible: backend.layoutMode === "horizontal"
                Layout.preferredWidth: 94
                Layout.preferredHeight: 24
                radius: 8
                color: "#182233"

                Label {
                    anchors.centerIn: parent
                    text: backend.selectedFrameCount + " frames"
                    color: "#8ea0bb"
                    font.pixelSize: 10
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

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: backend.layoutMode === "horizontal" ? 165 : -1
            Layout.fillHeight: backend.layoutMode === "individual"
            radius: 12
            color: "#080c13"
            border.color: "#1c293b"
            clip: true

            Image {
                id: preview
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
                x: preview.x
                y: preview.y + backend.cropTop * preview.height / Math.max(1, preview.sourceSize.height)
                width: preview.width
                height: 2
                color: "#25a7ff"
            }

            Rectangle {
                visible: backend.frameCount > 0 && backend.cropBottom > 0
                x: preview.x
                y: preview.y + preview.height - backend.cropBottom * preview.height / Math.max(1, preview.sourceSize.height)
                width: preview.width
                height: 2
                color: "#ff6682"
            }

            Label {
                anchors.centerIn: parent
                visible: backend.frameCount === 0
                text: "Analiza un video para empezar"
                color: "#59677c"
            }
        }

        Slider {
            Layout.fillWidth: true
            Layout.preferredHeight: 26
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
                text: "Agregar frame"
                enabled: backend.frameCount > 0
                         && !backend.busy
                         && !backend.currentFrameSelected
                onClicked: backend.toggleCurrentFrameSelection()
            }

            Button {
                Layout.preferredWidth: 92
                text: "Vaciar"
                enabled: backend.selectedFrameCount > 0 && !backend.busy
                onClicked: backend.clearFrameSelection()
            }

            Label {
                Layout.fillWidth: true
                text: backend.selectedFrameCount === 0
                      ? "Elige un frame y agrégalo."
                      : "Los frames se colocan en el orden seleccionado."
                color: "#77879f"
                elide: Text.ElideRight
            }
        }

        RowLayout {
            visible: backend.layoutMode === "horizontal"
            Layout.fillWidth: true
            Layout.preferredHeight: 76
            spacing: 8

            Label {
                Layout.preferredWidth: 48
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
                    width: 90
                    height: 70
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
                        height: 20
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

            Label {
                visible: backend.selectedFrameCount === 0
                Layout.fillWidth: true
                text: "Aquí aparecerán los frames seleccionados."
                color: "#59677c"
            }
        }

        Rectangle {
            visible: backend.layoutMode === "horizontal" && backend.joinCount > 0
            Layout.fillWidth: true
            Layout.preferredHeight: 78
            radius: 10
            color: "#0d1522"
            border.color: "#1b2a3f"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 5

                RowLayout {
                    Layout.fillWidth: true

                    Button {
                        Layout.preferredWidth: 30
                        Layout.preferredHeight: 24
                        text: "‹"
                        enabled: backend.currentJoin > 0
                        onClicked: backend.previousJoin()
                    }

                    Label {
                        Layout.preferredWidth: 116
                        text: backend.currentJoinLabel
                        color: "#dbe5f2"
                        font.pixelSize: 11
                        font.bold: true
                    }

                    Button {
                        Layout.preferredWidth: 30
                        Layout.preferredHeight: 24
                        text: "›"
                        enabled: backend.currentJoin < backend.joinCount - 1
                        onClicked: backend.nextJoin()
                    }

                    Item { Layout.fillWidth: true }

                    Label {
                        text: backend.currentAutoOverlap > 0
                              ? ("Auto " + backend.currentAutoOverlap + " px")
                              : "Detectando…"
                        color: "#77879f"
                        font.pixelSize: 10
                    }

                    Button {
                        Layout.preferredWidth: 46
                        Layout.preferredHeight: 24
                        text: "Auto"
                        onClicked: backend.resetCurrentOverlap()
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Label {
                        text: "Solape"
                        color: "#8290a6"
                        font.pixelSize: 10
                    }

                    Slider {
                        Layout.fillWidth: true
                        from: Math.max(8, Math.round(backend.montageFrameWidth * 0.05))
                        to: Math.max(16, Math.round(backend.montageFrameWidth * 0.90))
                        value: backend.currentOverlap
                        enabled: backend.montageFrameWidth > 0 && !backend.montageBusy
                        onMoved: backend.setCurrentOverlap(value)
                    }

                    Label {
                        Layout.preferredWidth: 72
                        text: backend.currentOverlap > 0
                              ? backend.currentOverlap + " px"
                              : "—"
                        color: "#cbd5e3"
                        font.pixelSize: 10
                        horizontalAlignment: Text.AlignRight
                    }

                    Label {
                        Layout.preferredWidth: 54
                        text: backend.currentJoinConfidence > 0
                              ? Math.round(backend.currentJoinConfidence * 100) + "%"
                              : "—"
                        color: "#6f8199"
                        font.pixelSize: 10
                    }
                }
            }
        }

        Rectangle {
            visible: backend.layoutMode === "horizontal"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 150
            radius: 12
            color: "#080c13"
            border.color: "#1c293b"
            clip: true

            Flickable {
                id: montageView
                anchors.fill: parent
                anchors.margins: 8
                visible: backend.montagePreviewSource !== ""
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                flickableDirection: Flickable.HorizontalFlick
                contentWidth: montageImage.width + 16
                contentHeight: height

                Image {
                    id: montageImage
                    x: 8
                    y: 8
                    height: Math.max(1, montageView.height - 16)
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
                running: backend.montageBusy
                visible: running
                width: 30
                height: 30
            }

            Label {
                anchors.centerIn: parent
                visible: !backend.montageBusy && backend.montagePreviewSource === ""
                text: backend.selectedFrameCount < 2
                      ? "Selecciona al menos 2 frames para comenzar."
                      : "Buscando la zona repetida…"
                color: "#59677c"
                horizontalAlignment: Text.AlignHCenter
            }

            Rectangle {
                visible: backend.montagePreviewSource !== ""
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.margins: 12
                width: 120
                height: 22
                radius: 7
                color: "#111827"

                Label {
                    anchors.centerIn: parent
                    text: "Reconstrucción"
                    color: "#8ea0bb"
                    font.pixelSize: 9
                }
            }
        }
    }
}
