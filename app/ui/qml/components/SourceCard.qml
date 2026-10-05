import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Rectangle {
    id: root
    Layout.fillWidth: true
    Layout.preferredHeight: 170
    radius: 16
    color: "#111827"
    border.color: "#1d2a3c"

    property string sourceMode: "YouTube"
    property string localName: ""

    FileDialog {
        id: videoDialog
        title: "Seleccionar video"
        nameFilters: ["Videos (*.mp4 *.mkv *.avi *.mov *.webm *.m4v)", "Todos los archivos (*)"]
        fileMode: FileDialog.OpenFile
        onAccepted: {
            backend.setLocalVideoUrl(selectedFile)
            root.localName = selectedFile.toLocalFile().split("/").pop()
        }
    }

    function switchMode(mode) {
        sourceMode = mode
        backend.reset()
        localName = ""
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 12

        RowLayout {
            Layout.fillWidth: true

            Label {
                text: "Fuente"
                color: "#f4f7fb"
                font.pixelSize: 16
                font.bold: true
            }

            Item { Layout.fillWidth: true }

            Repeater {
                model: ["YouTube", "Video local"]

                delegate: Rectangle {
                    Layout.preferredWidth: 112
                    Layout.preferredHeight: 34
                    radius: 9
                    color: root.sourceMode === modelData ? "#1d6fff" : "#182233"

                    MouseArea {
                        anchors.fill: parent
                        enabled: !backend.busy
                        onClicked: root.switchMode(modelData)
                    }

                    Label {
                        anchors.centerIn: parent
                        text: modelData
                        color: root.sourceMode === modelData ? "white" : "#8c9ab0"
                        font.pixelSize: 12
                    }
                }
            }
        }

        DropArea {
            id: dropArea
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            enabled: root.sourceMode === "Video local" && !backend.busy

            Rectangle {
                anchors.fill: parent
                radius: 10
                color: "#0d1522"
                border.color: dropArea.containsDrag ? "#2f85ff" : "#273752"
                border.width: dropArea.containsDrag ? 2 : 1

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10

                    TextField {
                        id: urlField
                        visible: root.sourceMode === "YouTube"
                        Layout.fillWidth: true
                        placeholderText: "Pega aquí la URL de YouTube"
                        color: "#e8edf5"
                        placeholderTextColor: "#5e6c82"
                        background: Rectangle {
                            radius: 8
                            color: "#111a28"
                            border.color: "#26364e"
                        }
                        onTextChanged: backend.setSourceText(text)
                    }

                    Label {
                        visible: root.sourceMode === "Video local"
                        Layout.fillWidth: true
                        text: root.localName === "" ? "Arrastra un video aquí o selecciónalo" : root.localName
                        color: root.localName === "" ? "#69778d" : "#d6deeb"
                        elide: Text.ElideMiddle
                    }

                    Button {
                        visible: root.sourceMode === "Video local"
                        text: "Subir video"
                        onClicked: videoDialog.open()
                    }
                }

                Label {
                    anchors.centerIn: parent
                    visible: root.sourceMode === "Video local" && dropArea.containsDrag
                    text: "Suelta el video aquí"
                    color: "#7db0ff"
                    font.bold: true
                }
            }

            onDropped: {
                if (drop.hasUrls) {
                    backend.setLocalVideoUrl(drop.urls[0])
                    root.localName = drop.urls[0].toLocalFile().split("/").pop()
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true

            Button {
                text: "Analizar video"
                enabled: !backend.busy
                onClicked: {
                    if (root.sourceMode === "YouTube")
                        backend.setSourceText(urlField.text)
                    backend.analyze()
                }
            }

            Label {
                visible: backend.frameCount > 0
                text: backend.frameCount + " frames preparados"
                color: "#6f8199"
                Layout.leftMargin: 8
            }

            Item { Layout.fillWidth: true }
        }
    }
}
