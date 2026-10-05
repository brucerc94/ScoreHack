import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Rectangle {
    id: root
    Layout.fillWidth: true
    Layout.preferredHeight: 125
    radius: 15
    color: "#111827"
    border.color: "#1d2a3c"

    property string sourceMode: "YouTube"
    property string localName: ""

    function localPath(urlValue) {
        var value = String(urlValue)
        if (value.indexOf("file:///") === 0)
            value = value.substring(8)
        return decodeURIComponent(value)
    }

    function localFileName(urlValue) {
        return localPath(urlValue).replace(/\\/g, "/").split("/").pop()
    }

    function switchMode(mode) {
        sourceMode = mode
        backend.reset()
        localName = ""
    }

    FileDialog {
        id: videoDialog
        title: "Seleccionar video"
        nameFilters: [
            "Videos (*.mp4 *.mkv *.avi *.mov *.webm *.m4v)",
            "Todos los archivos (*)"
        ]
        fileMode: FileDialog.OpenFile

        onAccepted: {
            var path = root.localPath(selectedFile)
            backend.setLocalVideo(path)
            root.localName = root.localFileName(selectedFile)
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 9

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 28

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0

                Label {
                    text: "1. Fuente"
                    color: "#f4f7fb"
                    font.pixelSize: 16
                    font.bold: true
                }

                Label {
                    text: backend.frameCount > 0
                          ? backend.frameCount + " frames preparados"
                          : "Selecciona el video que contiene la partitura"
                    color: "#6f8098"
                    font.pixelSize: 10
                }
            }

            RowLayout {
                spacing: 6

                Rectangle {
                    Layout.preferredWidth: 98
                    Layout.preferredHeight: 32
                    radius: 8
                    color: root.sourceMode === "YouTube" ? "#1d6fff" : "#182233"

                    MouseArea {
                        anchors.fill: parent
                        enabled: !backend.busy
                        onClicked: root.switchMode("YouTube")
                    }

                    Label {
                        anchors.centerIn: parent
                        text: "YouTube"
                        color: root.sourceMode === "YouTube" ? "white" : "#8292aa"
                        font.pixelSize: 11
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 105
                    Layout.preferredHeight: 32
                    radius: 8
                    color: root.sourceMode === "Video local" ? "#1d6fff" : "#182233"

                    MouseArea {
                        anchors.fill: parent
                        enabled: !backend.busy
                        onClicked: root.switchMode("Video local")
                    }

                    Label {
                        anchors.centerIn: parent
                        text: "Video local"
                        color: root.sourceMode === "Video local" ? "white" : "#8292aa"
                        font.pixelSize: 11
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            spacing: 8

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 9
                color: "#0d1522"
                border.color: "#26364e"

                TextField {
                    id: urlField
                    visible: root.sourceMode === "YouTube"
                    anchors.fill: parent
                    anchors.margins: 1
                    placeholderText: "Pega aquí la URL de YouTube"
                    color: "#e8edf5"
                    placeholderTextColor: "#5c6e87"
                    font.pixelSize: 12
                    background: Rectangle {
                        color: "transparent"
                    }
                    onTextChanged: backend.setSourceText(text)
                }

                Label {
                    visible: root.sourceMode === "Video local"
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    text: root.localName === ""
                          ? "Arrastra aquí el video o selecciónalo"
                          : root.localName
                    color: root.localName === "" ? "#718199" : "#dbe5f2"
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideMiddle
                    font.pixelSize: 12
                }

                DropArea {
                    id: dropArea
                    anchors.fill: parent
                    enabled: root.sourceMode === "Video local" && !backend.busy

                    Rectangle {
                        anchors.fill: parent
                        visible: dropArea.containsDrag
                        radius: 8
                        color: "#16345b"
                        opacity: 0.65
                    }

                    Label {
                        anchors.centerIn: parent
                        visible: dropArea.containsDrag
                        text: "Suelta el video aquí"
                        color: "#9bc1ff"
                        font.bold: true
                    }

                    onDropped: {
                        if (drop.hasUrls) {
                            var path = root.localPath(drop.urls[0])
                            backend.setLocalVideo(path)
                            root.localName = root.localFileName(drop.urls[0])
                        }
                    }
                }
            }

            Button {
                visible: root.sourceMode === "Video local"
                Layout.preferredWidth: 112
                Layout.fillHeight: true
                text: "Seleccionar"
                onClicked: videoDialog.open()
            }

            Button {
                visible: root.sourceMode === "YouTube"
                Layout.preferredWidth: 132
                Layout.fillHeight: true
                text: "Analizar video"
                enabled: !backend.busy
                onClicked: backend.analyze()
            }
        }

        Button {
            visible: root.sourceMode === "Video local"
            Layout.preferredWidth: 132
            Layout.preferredHeight: 34
            text: "Analizar video"
            enabled: !backend.busy && root.localName !== ""
            onClicked: backend.analyze()
        }
    }
}
