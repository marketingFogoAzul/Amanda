import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.stream.Collectors;

/**
 * Classe utilitária responsável por ler, parsear e converter dados de arquivos CSV
 * em estruturas de dados Java (Listas de Mapas), facilitando o manuseio.
 * Pode ser estendida para suportar XLS/XLSX se integrar bibliotecas externas (ex: Apache POI).
 *
 * Esta classe é fundamental para processamento de dados brutos de importação.
 */
public class conversorcsv { // Nome da classe interna ajustado para o nome do arquivo

    private static final String DEFAULT_SEPARATOR = ",";
    private static final String LINE_BREAK = "\n";

    /**
     * Lê um arquivo CSV e retorna uma lista de mapas, onde cada mapa representa uma linha
     * e associa o nome da coluna (cabeçalho) ao seu valor.
     *
     * @param filePath O caminho completo para o arquivo CSV.
     * @param separator O delimitador usado no arquivo (ex: "," ou ";").
     * @return List<Map<String, String>> Lista de linhas processadas.
     * @throws IOException Se houver erro na leitura do arquivo.
     */
    public List<Map<String, String>> lerCsvParaMapa(String filePath, String separator) throws IOException {
        List<Map<String, String>> records = new ArrayList<>();
        
        try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
            String headerLine = br.readLine();
            if (headerLine == null) {
                return records;
            }
            
            // 1. Processa o cabeçalho (nomes das colunas)
            List<String> headers = parseLine(headerLine, separator).stream()
                                                                  .map(String::trim)
                                                                  .collect(Collectors.toList());

            String line;
            // 2. Processa cada linha de dados
            while ((line = br.readLine()) != null) {
                if (line.trim().isEmpty()) continue;
                
                List<String> values = parseLine(line, separator);
                
                // Cria o mapa da linha (Coluna: Valor)
                Map<String, String> record = new HashMap<>();
                for (int i = 0; i < headers.size() && i < values.size(); i++) {
                    record.put(headers.get(i), values.get(i).trim());
                }
                records.add(record);
            }
        }
        return records;
    }

    /**
     * Método auxiliar para dividir uma linha em valores, tratando aspas duplas.
     * Nota: Esta é uma implementação simplificada de parser CSV.
     *
     * @param line A string da linha.
     * @param separator O delimitador.
     * @return List<String> Lista de valores.
     */
    private List<String> parseLine(String line, String separator) {
        // Usa uma expressão regular simples para separar por delimitador,
        // mas não lida totalmente com campos que contêm o próprio delimitador dentro de aspas.
        // É um parser adequado para planilhas limpas.
        return Arrays.asList(line.split(separator, -1));
    }

    /**
     * Converte uma lista de mapas de volta para o formato CSV.
     * Útil para exportação de dados após o processamento.
     *
     * @param records Os dados a serem exportados (List<Map<String, String>>).
     * @param headers A ordem e nomes dos cabeçalhos a serem incluídos.
     * @param separator O delimitador a ser usado.
     * @return String Retorna o conteúdo formatado em CSV.
     */
    public String converterMapaParaCsv(List<Map<String, String>> records, List<String> headers, String separator) {
        StringBuilder csvData = new StringBuilder();

        // 1. Adiciona o cabeçalho
        csvData.append(headers.stream().collect(Collectors.joining(separator))).append(LINE_BREAK);

        // 2. Adiciona os dados
        for (Map<String, String> record : records) {
            String line = headers.stream()
                .map(header -> {
                    String value = record.getOrDefault(header, "");
                    // Envolve em aspas se contiver separador ou linha nova
                    if (value.contains(separator) || value.contains(LINE_BREAK)) {
                        // Trata aspas duplas internas duplicando-as
                        value = value.replace("\"", "\"\"");
                        return "\"" + value + "\"";
                    }
                    return value;
                })
                .collect(Collectors.joining(separator));
            csvData.append(line).append(LINE_BREAK);
        }

        return csvData.toString();
    }
}