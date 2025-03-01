import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import java.io.*;
import java.util.*;
import java.util.logging.*;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

public class BCSTEST extends JFrame {

    private static final String DEFAULT_CSV_FILENAME = "current_state.csv";
    private static final String FLOORS_FILE = "floors.json";
    private static final Logger logger = Logger.getLogger(BCSTEST.class.getName());
    private final Map<String, Map<String, java.util.List<Map<String, String>>>> roomStatus = new HashMap<>();
    private Map<String, Map<String, Map<String, Integer>>> floors = new HashMap<>();
    private String csvFile;
    private String currentFloor;

    public BCSTEST() {
        setTitle("IESLH Building Check");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new BorderLayout());

        // Load floors data
        floors = loadFloorsData();

        // Create main panel
        JPanel mainPanel = new JPanel();
        mainPanel.setLayout(new GridLayout(2, 1));

        JButton newCheckButton = createButton("New Check", e -> newCheck());
        JButton resumeCheckButton = createButton("Resume Check", e -> resumeCheck());

        mainPanel.add(newCheckButton);
        mainPanel.add(resumeCheckButton);

        add(mainPanel, BorderLayout.CENTER);
        pack();
        setVisible(true);
    }

    private JButton createButton(String text, ActionListener action) {
        JButton button = new JButton(text);
        button.addActionListener(action);
        return button;
    }

    private Map<String, Map<String, Map<String, Integer>>> loadFloorsData() {
        try (Reader reader = new FileReader(FLOORS_FILE)) {
            return new Gson().fromJson(reader, new TypeToken<Map<String, Map<String, Map<String, Integer>>>>() {}.getType());
        } catch (FileNotFoundException e) {
            logger.log(Level.SEVERE, FLOORS_FILE + " not found.", e);
            return new HashMap<>();
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Error decoding " + FLOORS_FILE, e);
            return new HashMap<>();
        }
    }

    private void newCheck() {
        String currentDate = new java.text.SimpleDateFormat("yyyy-MM-dd").format(new Date());
        csvFile = "check_results_" + currentDate + ".csv";

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(csvFile))) {
            writer.write("Room,Item,Index,Status,Notes\n"); // Write the header row
            logger.log(Level.INFO, "New check file created: {0}", csvFile);
        } catch (IOException e) {
            logger.log(Level.SEVERE, "Error creating new check file: ", e);
        }

        // Remove any previous state
        File defaultCsvFile = new File(DEFAULT_CSV_FILENAME);
        if (defaultCsvFile.exists()) {
            defaultCsvFile.delete();
        }

        initializeRoomStatus();
        floorSelection();
    }

    private void resumeCheck() {
        File[] csvFiles = new File(".").listFiles((dir, name) -> name.startsWith("check_results_") && name.endsWith(".csv"));
        if (csvFiles == null || csvFiles.length == 0) {
            showPopup("Error", "No previous check found. Ensure check files exist in the current directory.");
            return;
        }

        csvFile = Arrays.stream(csvFiles)
                .max(Comparator.comparingLong(File::lastModified))
                .map(File::getName)
                .orElse(null);
        logger.log(Level.INFO, "Resuming from file: {0}", csvFile);

        loadPreviousCheck();
        loadCurrentState();
        floorSelection();
    }

    private void showPopup(String title, String content) {
        JOptionPane.showMessageDialog(this, content, title, JOptionPane.INFORMATION_MESSAGE);
    }

    private void initializeRoomStatus() {
        roomStatus.clear();
        for (String floor : floors.keySet()) {
            for (String room : floors.get(floor).keySet()) {
                Map<String, java.util.List<Map<String, String>>> roomDetails = new HashMap<>();
                for (Map.Entry<String, Integer> entry : floors.get(floor).get(room).entrySet()) {
                    String item = entry.getKey().toLowerCase();
                    int count = entry.getValue();
                    java.util.List<Map<String, String>> statuses = new ArrayList<>();
                    for (int i = 0; i < count; i++) {
                        statuses.add(new HashMap<>()); // Initialize with empty status
                    }
                    roomDetails.put(item, statuses);
                }
                roomStatus.put(room, roomDetails);
            }
        }
    }

    private void loadPreviousCheck() {
        initializeRoomStatus(); // Reset room status
        try (BufferedReader reader = new BufferedReader(new FileReader(csvFile))) {
            reader.readLine(); // Skip header
            logger.log(Level.INFO, "Loading data from {0}", csvFile);
            String line;
            while ((line = reader.readLine()) != null) {
                String[] row = line.split(",");
                if (row.length >= 5) {
                    try {
                        String room = row[0];
                        String itemType = row[1].toLowerCase();
                        int itemIndex = Integer.parseInt(row[2]);
                        String status = row[3];
                        String notes = row[4];

                        if (roomStatus.containsKey(room) && roomStatus.get(room).containsKey(itemType)) {
                            roomStatus.get(room).get(itemType).get(itemIndex).put("status", status);
                            roomStatus.get(room).get(itemType).get(itemIndex).put("notes", notes);
                            logger.log(Level.INFO, "Loaded status: Room {0}, {1} {2} - {3}, Notes: {4}", new Object[]{room, itemType, itemIndex + 1, status, notes});
                        } else {
                            logger.log(Level.WARNING, "Room {0} or item {1} not found in configuration.", new Object[]{room, itemType});
                        }
                    } catch (NumberFormatException e) {
                        logger.log(Level.SEVERE, "Skipping invalid row in file: " + line, e);
                    }
                } else {
                    logger.log(Level.WARNING, "Incomplete row: {0}", line);
                }
            }
        } catch (IOException e) {
            logger.log(Level.SEVERE, "Error loading previous check file: ", e);
        }
    }

    private void loadCurrentState() {
        File currentStateFile = new File(DEFAULT_CSV_FILENAME);
        if (!currentStateFile.exists()) {
            logger.warning("Current state file not found.");
            return;
        }

        try (BufferedReader reader = new BufferedReader(new FileReader(currentStateFile))) {
            reader.readLine(); // Skip header
            String line;
            while ((line = reader.readLine()) != null) {
                String[] row = line.split(",");
                if (row.length == 5) {
                    try {
                        String room = row[0];
                        String item = row[1];
                        int index = Integer.parseInt(row[2]);
                        String status = row[3];
                        String notes = row[4];

                        if (roomStatus.containsKey(room) && roomStatus.get(room).containsKey(item)) {
                            roomStatus.get(room).get(item).get(index).put("status", status);
                            roomStatus.get(room).get(item).get(index).put("notes", notes);
                            logger.log(Level.INFO, "Loaded status for Room {0}, {1} {2}: {3}, Notes: {4}", new Object[]{room, item, index + 1, status, notes});
                        } else {
                            logger.log(Level.WARNING, "Room {0} or item {1} not found in the current configuration.", new Object[]{room, item});
                        }
                    } catch (NumberFormatException e) {
                        logger.log(Level.SEVERE, "ValueError while processing row: " + line, e);
                    }
                } else {
                    logger.log(Level.WARNING, "Skipping invalid row in current state: {0}", line);
                }
            }
        } catch (IOException e) {
            logger.log(Level.SEVERE, "Error loading current state: ", e);
        }
    }

    private void floorSelection() {
        StringBuilder floorSelection = new StringBuilder("Select Floor:\n");
        for (String floor : floors.keySet()) {
            floorSelection.append(floor).append("\n");
        }
        showPopup("Select Floor", floorSelection.toString());
    }

    private void checkRoom(String room) {
        // Example call to saveResult method
        saveResult(room, "item", 0, "Checked");

        // Example call to showNotesInput method
        showNotesInput(room, "item", 0);
        StringBuilder content = new StringBuilder("Check Room " + room + ":\n");
        Map<String, Integer> roomDetails = floors.get(currentFloor).get(room);

        for (Map.Entry<String, Integer> entry : roomDetails.entrySet()) {
            String item = entry.getKey();
            int count = entry.getValue();
            for (int i = 0; i < count; i++) {
                String itemStatus = roomStatus.get(room).get(item.toLowerCase()).get(i).get("status");
                content.append(item).append(" ").append(i + 1).append(": ").append(itemStatus != null ? itemStatus : "Not checked").append("\n");
            }
        }
        showPopup("Check Room " + room, content.toString());
    }

    private void saveResult(String room, String item, int index, String result) {
        roomStatus.get(room).get(item).get(index).put("status", result);
        saveCurrentState();
        checkRoom(room);
    }

    private void saveCurrentState() {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(DEFAULT_CSV_FILENAME))) {
            writer.write("Room,Item,Index,Status,Notes\n"); // Header
            for (Map.Entry<String, Map<String, java.util.List<Map<String, String>>>> roomEntry : roomStatus.entrySet()) {
                String room = roomEntry.getKey();
                for (Map.Entry<String, java.util.List<Map<String, String>>> itemEntry : roomEntry.getValue().entrySet()) {
                    String item = itemEntry.getKey();
                    java.util.List<Map<String, String>> statuses = itemEntry.getValue();
                    for (int index = 0; index < statuses.size(); index++) {
                        Map<String, String> status = statuses.get(index);
                        if (status.get("status") != null) { // Save only non-empty statuses
                            writer.write(String.join(",", room, item, String.valueOf(index), status.get("status"), status.get("notes") != null ? status.get("notes") : "") + "\n");
                        }
                    }
                }
            }
            logger.info("Current state saved successfully.");
        } catch (IOException e) {
            logger.log(Level.SEVERE, "Error saving current state: ", e);
        }
    }

    private void showNotesInput(String room, String item, int index) {
        JTextArea textArea = new JTextArea();
        String existingNote = roomStatus.get(room).get(item).get(index).get("notes");
        textArea.setText(existingNote != null ? existingNote : "");

        JButton saveButton = new JButton("Save");
        saveButton.addActionListener(e -> {
            saveNotes(room, item, index, textArea.getText());
            ((JDialog) SwingUtilities.getWindowAncestor(saveButton)).dispose(); // Close the notes input dialog
        });

        JPanel panel = new JPanel(new BorderLayout());
        panel.add(new JLabel("Enter your notes here:"), BorderLayout.NORTH);
        panel.add(new JScrollPane(textArea), BorderLayout.CENTER);
        panel.add(saveButton, BorderLayout.SOUTH);

        JDialog dialog = new JDialog(this, "Notes Input", true);
        dialog.setContentPane(panel);
        dialog.pack();
        dialog.setVisible(true);
    }

    private void saveNotes(String room, String item, int index, String notes) {
        roomStatus.get(room).get(item).get(index).put("notes", notes);
        logger.log(Level.INFO, "Saved notes for Room {0}, {1} {2}: {3}", new Object[]{room, item, index + 1, notes});
        saveCurrentState();
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(BCSTEST::new);
    }
}