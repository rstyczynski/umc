/*
    Oracle SQL Query Metric Collector, tomas@vitvar.com, March 2018
    This script runs in SQLcl, use sql-collector script to run it
*/

// various java libraries used by this script 
var Thread = Java.type("java.lang.Thread");
var System = Java.type("java.lang.System");
var Paths = Java.type("java.nio.file.Paths");
var Files = Java.type("java.nio.file.Files");

function errorAndExit(text) {
  print(text);
  print("");
  System.exit(1);  
}

// get the sqlcDir - must be set as env variable
var sqlcDir = System.getenv("sqlcDir");
if (!sqlcDir || sqlcDir === "")
  errorAndExit("The environment variable $sqlcDir has not been set! Are you running sql-collector script?");

load(sqlcDir + "/libs/ArgumentsParser.js");

var programName = 
  "Oracle SQL query metric collector";

var optionDef = [
  { name: 'connect',            type: String,    required: true,  desc : "DB connection string." },
  { name: 'query',              type: String,    required: true,  desc : "SQL query file." },
  { name: 'count',              type: Number,    required: true,  desc : "Number of iterations the query will run." },
  { name: 'interval',           type: Number,    required: true,  desc : "Delay in seconds betwen iterations." },
  { name: 'noHeaders',                           required: false, desc : "Headers will not be written to the output." },  
  { name: 'showSQLErrors',                       required: false, desc : "SQL errors will be written to the output." },  
  { name: '#([a-zA-Z0-9_\\-\\*\\+\\.]+)',
                                type: String,    required: false, desc : "A regular expression to replace a string with a value in the query." }, 
  { name: 'test',                                required: false, desc : "Test and be verbose, will run only one iteration of the query." },
]

// clean arguments
// when arguments are passed in sqljs, the first argument is the script name
var cmdargs = [];
for (var i = 1; i < args.length; i++)
  cmdargs.push(args[i]);

// helper functions
function runSQL(statement) {
  sqlcl.setStmt(statement); sqlcl.run();
}

function loadSQLTemplate(file) {
  var lines = Files.readAllLines(Paths.get(file), Java.type('java.nio.charset.StandardCharsets').UTF_8);  
  var s = ""; for (var i = 0; i < lines.length; i++) s += lines[i] + "\n";
  return s;
}

// main 

try {

  // parse command line arguments and display help if there is error
  var argv = parseArgsAndHelp(programName, cmdargs, optionDef);

  if (argv) {

    if (argv.test) {
      print("* sql-collector executed in the test mode.");
      print("* Arguments parsed as JSON object:");
      print(JSON.stringify(argv));
      print('');
    }

    if(!Files.exists(Paths.get(argv.query.value)))
        errorAndExit("The sql query file " + argv.query.value + " does not exist!");

    // load sql query from the input file
    var sql = loadSQLTemplate(argv.query.value);

    // replace variables in the query
    for (var arg in argv) {
      if (argv[arg].name.startsWith("#"))
        sql = sql.replace(new RegExp(argv[arg].name.substr(1), 'g'), argv[arg].value);  
    }

    if (argv.test) {
      print("* SQL query:");
      print(sql);
      print('');
    }

    function runSQLIteration(iteration) {
      runSQL("SET HEADING " + (iteration > 1 || argv.noHeaders ? "OFF" : "ON"));
      runSQL(sql);
    }

    // global SQL params
    runSQL("SET SQLFORMAT CSV");
    runSQL("SET SQLBLANKLINES ON");
    runSQL("SET TRIMSPOOL ON");

    if (!argv.showSQLErrors && !argv.test) {
      runSQL("SET ECHO OFF");
      runSQL("SET FEEDBACK OFF");
    }

    if (argv.test) {
      print("* Connecting to the DB...");
    }

    // connect to the DB
    runSQL("CONNECT " + argv.connect.value);

    // run only once in the test mode
    if (argv.test) {
      print("* Running one iteration of the query...");
      argv.count.value = 1;
    }

    // run SQL count times with interval bettwen runs
    for (var i = 0; i < argv.count.value; i++) {
      runSQLIteration(i + 1);

      if (i < argv.count.value - 1)
        Thread.sleep(argv.interval.value * 1000);
    }

  }
} catch (e) {
  errorAndExit(e);
}
