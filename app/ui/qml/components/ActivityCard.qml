import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    Layout.fillWidth: true
    Layout.preferredHeight: 135
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
                text: "Actividad"
                color: "#f4f7fb"
                font.pixelSize: 16
                font.bold: true
            }

            Item { Layout.fillWidth: true }

            Label {
                text: Math.round(backend.progress * 100) + "%"
                color: "#71829a"
            }
        }

        ProgressBar {
            Layout.fillWidth: true
            value: backend.progress
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            TextArea {
                id: logArea
                readOnly: true
                wrapMode: TextArea.Wrap
                color: "#8998ad"
                font.pixelSize: 11
                background: Rectangle { color: "transparent" }
            }
        }
    }

    Connections {
        target: backend
        function onLogMessage(message) {
            logArea.text += message + "\n"
        }
    }
}
