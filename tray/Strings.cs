using System.Collections.Generic;
using System.Globalization;

namespace RhinoMCPTray
{
    /// <summary>
    /// Tray texts in English, Italian, French, German or Spanish: Rhino's own
    /// UI language when a Rhino reports one, else the Windows display language,
    /// else English. To add a language, copy the English block into Languages.
    /// </summary>
    class Strings
    {
        public string ShowInstances, CloseIcon, NoneConnectedTip, ClickHint, EmptyTitle, EmptyHint, NoEntry,
                      Port, Since, Untitled, NoDefinition, NoSession, SharedRhino, NoCommands,
                      SessionOne, SessionMany, CommandOne, CommandMany,
                      JustNow, SecondsAgo, MinutesAgo, HoursAgo;

        // Lazy: a field initializer here would run before English and Languages below.
        private static Strings current;
        public static Strings Current => current ?? (current = Pick(CultureInfo.CurrentUICulture));

        /// <summary>Switches to the given culture name ("it-IT"), if it is one we have.</summary>
        public static void Use(string cultureName)
        {
            if (string.IsNullOrEmpty(cultureName)) return;
            try
            {
                current = Pick(CultureInfo.GetCultureInfo(cultureName));
            }
            catch (CultureNotFoundException)
            {
            }
        }

        public string Sessions(int count) => string.Format(count == 1 ? SessionOne : SessionMany, count);
        public string Commands(int count) => string.Format(count == 1 ? CommandOne : CommandMany, count);

        private static Strings Pick(CultureInfo culture)
        {
            for (var c = culture; !string.IsNullOrEmpty(c?.Name); c = c.Parent)
            {
                if (Languages.TryGetValue(c.TwoLetterISOLanguageName, out var strings)) return strings;
            }
            return English;
        }

        private static readonly Strings English = new Strings
        {
            ShowInstances = "Show Rhino instances",
            CloseIcon = "Close tray icon",
            NoneConnectedTip = "RhinoMCP: no Rhino connected",
            ClickHint = "Click a Rhino to bring it to the front",
            EmptyTitle = "No Rhino is connected",
            EmptyHint = "Run mcpstart in Rhino to list it here",
            NoEntry = "no MCP entry",
            Port = "Port {0}",
            Since = "since {0}",
            Untitled = "Untitled",
            NoDefinition = "no definition open",
            NoSession = "No Claude session connected",
            SharedRhino = "{0} Claude sessions share this Rhino",
            NoCommands = "connected, no commands yet",
            SessionOne = "{0} session",
            SessionMany = "{0} sessions",
            CommandOne = "{0} command",
            CommandMany = "{0} commands",
            JustNow = "just now",
            SecondsAgo = "{0} s ago",
            MinutesAgo = "{0} min ago",
            HoursAgo = "{0} h ago",
        };

        private static readonly Dictionary<string, Strings> Languages = new Dictionary<string, Strings>
        {
            ["en"] = English,
            ["it"] = new Strings
            {
                ShowInstances = "Mostra le istanze di Rhino",
                CloseIcon = "Chiudi l'icona",
                NoneConnectedTip = "RhinoMCP: nessun Rhino collegato",
                ClickHint = "Fai clic su un Rhino per portarlo in primo piano",
                EmptyTitle = "Nessun Rhino collegato",
                EmptyHint = "Esegui mcpstart in Rhino per vederlo qui",
                NoEntry = "nessun ingresso MCP",
                Port = "Porta {0}",
                Since = "dalle {0}",
                Untitled = "Senza titolo",
                NoDefinition = "nessuna definizione aperta",
                NoSession = "Nessuna sessione Claude collegata",
                SharedRhino = "{0} sessioni Claude usano questo Rhino",
                NoCommands = "collegata, ancora nessun comando",
                SessionOne = "{0} sessione",
                SessionMany = "{0} sessioni",
                CommandOne = "{0} comando",
                CommandMany = "{0} comandi",
                JustNow = "adesso",
                SecondsAgo = "{0} s fa",
                MinutesAgo = "{0} min fa",
                HoursAgo = "{0} h fa",
            },
            ["fr"] = new Strings
            {
                ShowInstances = "Afficher les instances Rhino",
                CloseIcon = "Fermer l'icône",
                NoneConnectedTip = "RhinoMCP : aucun Rhino connecté",
                ClickHint = "Cliquez sur un Rhino pour l'afficher",
                EmptyTitle = "Aucun Rhino connecté",
                EmptyHint = "Lancez mcpstart dans Rhino pour le voir ici",
                NoEntry = "aucune entrée MCP",
                Port = "Port {0}",
                Since = "depuis {0}",
                Untitled = "Sans titre",
                NoDefinition = "aucune définition ouverte",
                NoSession = "Aucune session Claude connectée",
                SharedRhino = "{0} sessions Claude partagent ce Rhino",
                NoCommands = "connectée, aucune commande",
                SessionOne = "{0} session",
                SessionMany = "{0} sessions",
                CommandOne = "{0} commande",
                CommandMany = "{0} commandes",
                JustNow = "à l'instant",
                SecondsAgo = "il y a {0} s",
                MinutesAgo = "il y a {0} min",
                HoursAgo = "il y a {0} h",
            },
            ["de"] = new Strings
            {
                ShowInstances = "Rhino-Instanzen anzeigen",
                CloseIcon = "Symbol schließen",
                NoneConnectedTip = "RhinoMCP: kein Rhino verbunden",
                ClickHint = "Klick auf ein Rhino holt es nach vorne",
                EmptyTitle = "Kein Rhino verbunden",
                EmptyHint = "mcpstart in Rhino ausführen, um es hier zu sehen",
                NoEntry = "kein MCP-Eintrag",
                Port = "Port {0}",
                Since = "seit {0}",
                Untitled = "Unbenannt",
                NoDefinition = "keine Definition geöffnet",
                NoSession = "Keine Claude-Sitzung verbunden",
                SharedRhino = "{0} Claude-Sitzungen teilen sich dieses Rhino",
                NoCommands = "verbunden, noch keine Befehle",
                SessionOne = "{0} Sitzung",
                SessionMany = "{0} Sitzungen",
                CommandOne = "{0} Befehl",
                CommandMany = "{0} Befehle",
                JustNow = "gerade eben",
                SecondsAgo = "vor {0} s",
                MinutesAgo = "vor {0} min",
                HoursAgo = "vor {0} h",
            },
            ["es"] = new Strings
            {
                ShowInstances = "Mostrar instancias de Rhino",
                CloseIcon = "Cerrar el icono",
                NoneConnectedTip = "RhinoMCP: ningún Rhino conectado",
                ClickHint = "Haz clic en un Rhino para traerlo al frente",
                EmptyTitle = "Ningún Rhino conectado",
                EmptyHint = "Ejecuta mcpstart en Rhino para verlo aquí",
                NoEntry = "sin entrada MCP",
                Port = "Puerto {0}",
                Since = "desde las {0}",
                Untitled = "Sin título",
                NoDefinition = "ninguna definición abierta",
                NoSession = "Ninguna sesión de Claude conectada",
                SharedRhino = "{0} sesiones de Claude comparten este Rhino",
                NoCommands = "conectada, aún sin comandos",
                SessionOne = "{0} sesión",
                SessionMany = "{0} sesiones",
                CommandOne = "{0} comando",
                CommandMany = "{0} comandos",
                JustNow = "ahora mismo",
                SecondsAgo = "hace {0} s",
                MinutesAgo = "hace {0} min",
                HoursAgo = "hace {0} h",
            },
        };
    }
}
