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

            Label {
                text: backend.layoutMode === "horizontal"
                      ? "Selector de frames"
                      : "Vista previa"
                color: "#f4f7fb"
                font.pixelSize: 16
                font.bold: true
            }

            Item { Layout.fillWidth: true }

            Label {
                text: backend.frameCount > 0
                      ? ("Frame " + (backend.currentFrame + 1) + " / " + backend.frameCount)
                      : "Sin video"
                color: "#70819a"
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: backend.layoutMode === "individual"
            Layout.preferredHeight: backend.layoutMode === "horizontal" ? 190 : -1
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
                Layout.preferredWidth: 100
                text: "Vaciar"
                enabled: backend.selectedFrameCount > 0 && !backend.busy
                onClicked: backend.clearFrameSelection()
            }

            Label {
                Layout.fillWidth: true
                text: backend.selectedFrameCount === 0
                      ? "Selecciona un frame y pulsa Agregar frame."
                      : backend.selectedFrameCount + " frames seleccionados"
                color: "#77879f"
                elide: Text.ElideRight
            }
        }

        ListView {
            visible: backend.layoutMode === "horizontal" && backend.selectedFrameCount > 0
            Layout.fillWidth: true
            Layout.preferredHeight: 72
            orientation: ListView.Horizontal
            spacing: 6
            clip: true
            model: backend.selectedFrameSources

            delegate: Rectangle {
                width: 92
                height: 68
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

        Rectangle {
            visible: backend.layoutMode === "horizontal"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 160
            radius: 12
            color: "#080c13"
            border.color: "#1c293b"
            clip: true

            ScrollView {
                anchors.fill: parent
                anchors.margins: 8
                clip: true
                ScrollBar.horizontal.policy: ScrollBar.AsNeeded
                ScrollBar.vertical.policy: ScrollBar.AsNeeded

                Image {
                    id: montageImage
                    source: backend.montagePreviewSource
                    asynchronous: true
                    cache: false
                    fillMode: Image.PreserveAspectFit
                    width: Math.max(sourceSize.width, parent.width)
                    height: Math.max(sourceSize.height, parent.height)
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
                      : "Preparando unión horizontal…"
                color: "#59677c"
                horizontalAlignment: Text.AlignHCenter
            }

            Label {
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                anchors.leftMargin: 10
                anchors.bottomMargin: 8
                text: backend.montagePreviewSource !== ""
                      ? "Previsualización horizontal"
                      : ""
                color: "#71829a"
                font.pixelSize: 10
            }
        }
    }
}
