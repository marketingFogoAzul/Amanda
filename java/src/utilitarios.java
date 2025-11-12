import java.math.BigDecimal;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.Locale;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Classe utilitária contendo métodos estáticos para operações comuns,
 * como formatação, validação básica e manipulação de strings.
 * Não deve conter lógica de negócio complexa (como fiscais ou I/O pesado).
 */
public class utilitarios { // Nome da classe interna ajustado para o nome do arquivo

    // Formato de moeda Brasileira: R$ 1.234,56
    private static final DecimalFormat DECIMAL_FORMAT_BR;
    private static final Pattern NUMBERS_ONLY_PATTERN = Pattern.compile("\\d+");

    static {
        // Configuração para formato monetário brasileiro (vírgula como decimal, ponto como milhar)
        DecimalFormatSymbols symbols = new DecimalFormatSymbols(new Locale("pt", "BR"));
        symbols.setDecimalSeparator(',');
        symbols.setGroupingSeparator('.');
        DECIMAL_FORMAT_BR = new DecimalFormat("#,##0.00", symbols);
    }

    /**
     * Formata um valor BigDecimal para o padrão monetário brasileiro (ex: "1.234,56").
     *
     * @param value O valor a ser formatado.
     * @return String Valor formatado.
     */
    public static String formatarMoeda(BigDecimal value) {
        if (value == null) {
            return "0,00";
        }
        return DECIMAL_FORMAT_BR.format(value);
    }

    /**
     * Remove todos os caracteres não-numéricos de uma string.
     * Útil para limpar CPF, CNPJ, telefone, etc.
     *
     * @param text A string de entrada.
     * @return String Contendo apenas dígitos.
     */
    public static String removerNaoNumericos(String text) {
        if (text == null) {
            return "";
        }
        Matcher matcher = NUMBERS_ONLY_PATTERN.matcher(text);
        StringBuilder sb = new StringBuilder();
        while (matcher.find()) {
            sb.append(matcher.group());
        }
        return sb.toString();
    }

    /**
     * Gera um identificador único universal (UUID) como string.
     *
     * @return String um UUID em formato padrão.
     */
    public static String gerarUUID() {
        return UUID.randomUUID().toString();
    }

    /**
     * Verifica se uma string é nula ou vazia após remover espaços em branco.
     *
     * @param str A string a ser verificada.
     * @return boolean True se a string estiver vazia ou for nula.
     */
    public static boolean isNullOrBlank(String str) {
        return str == null || str.trim().isEmpty();
    }

    /**
     * Limita o tamanho de uma string e adiciona reticências se o limite for ultrapassado.
     *
     * @param str A string original.
     * @param maxLength O comprimento máximo desejado.
     * @return String A string truncada ou original.
     */
    public static String truncarString(String str, int maxLength) {
        if (isNullOrBlank(str) || str.length() <= maxLength) {
            return str;
        }
        return str.substring(0, maxLength - 3) + "...";
    }

    /**
     * Converte um objeto String para BigDecimal, tratando formatos brasileiros (vírgula).
     *
     * @param valueStr String com o valor numérico (ex: "1.234,56").
     * @return BigDecimal O valor convertido, ou null em caso de erro.
     */
    public static BigDecimal stringToBigDecimal(String valueStr) {
        if (isNullOrBlank(valueStr)) {
            return null;
        }
        try {
            // Remove pontos de milhar e substitui vírgula por ponto para parse
            String cleanValue = valueStr.replace(".", "").replace(",", ".");
            return new BigDecimal(cleanValue);
        } catch (NumberFormatException e) {
            return null; // Retorna nulo se a string não for um número válido
        }
    }
}