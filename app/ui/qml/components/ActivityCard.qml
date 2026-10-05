import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    Layout.fillWidth: true
    Layout.preferredHeight: 88
    radius: 14
    color: "#111827"
    border.color: "#1d2a3c"

    RowLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 14

        ColumnLayout {
            Layout.preferredWidth: 150
            spacing: 3

            Label {
                text: "Activity"
                color: "#f4f7fb"
                font.pixelSize: 14
                font.bold: true
            }

            Label {
                text: Math.round(backend.progress * 100) + "%"
                color: "#70819a"
                font.pixelSize: 11
            }
        }

        ProgressBar {
            Layout.preferredWidth: 190
            Layout.preferredHeight: 8
            value: backend.progress
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            TextArea {
                id: logArea
                readOnly: true
                wrapMode: TextArea.NoWrap
                color: "#8190a8"
                font.pixelSize: 10
                background: Rectangle { color: "transparent" }
            }
        }
    }

    Connections {
        target: backend
        function onLogMessage(message) {
            logArea.text += message + "
"
            logArea.cursorPosition = logArea.length
        }
    }
}
