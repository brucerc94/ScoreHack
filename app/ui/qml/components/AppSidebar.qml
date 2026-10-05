import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#0e1420"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 8

        Label {
            text: "♫  ScoreCapture"
            color: "#f4f7fb"
            font.pixelSize: 22
            font.bold: true
            Layout.topMargin: 6
        }

        Label {
            text: "Sheet music extractor"
            color: "#71829a"
            font.pixelSize: 11
            Layout.bottomMargin: 20
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 46
            radius: 10
            color: "#1d6fff"

            Label {
                anchors.centerIn: parent
                text: "Extract sheet music"
                color: "white"
                font.pixelSize: 12
                font.bold: true
            }
        }

        Label {
            text: "WORKFLOW"
            color: "#607089"
            font.pixelSize: 10
            font.bold: true
            Layout.topMargin: 18
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            radius: 9
            color: "#182233"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                spacing: 8

                Label {
                    text: "01"
                    color: "#6fa3ff"
                    font.pixelSize: 10
                    font.bold: true
                }

                Label {
                    text: "Source"
                    color: "#d0d8e5"
                    font.pixelSize: 11
                }
            }
        }

        Label { text: "02  Crop & Reconstruction"; color: "#8b98ad"; font.pixelSize: 11 }
        Label { text: "03  Export PDF"; color: "#8b98ad"; font.pixelSize: 11 }

        Item { Layout.fillHeight: true }

        Label {
            text: "Processing runs in the background."
            color: "#5f6e84"
            font.pixelSize: 9
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }
}
