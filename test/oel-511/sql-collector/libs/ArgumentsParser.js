
/*  Simple arguments parser, tomas@vitvar.com, March 2018
    Definition of arguments is optionDefinitions object as per following example:

    var optionDef = [
      { name: 'query',              type: String,    required: true,  desc : "SQL query file." },
      { name: 'count',              type: Number,    required: true,  desc : "Number of iterations the query will run." },
      { name: 'interval',           type: Number,    required: true,  desc : "Delay in seconds betwen iterations." },
      { name: 'noHeaders',                           required: false, desc : "Headers will not be writen to the output." },  
      { name: 'showSQLErrors',                       required: false, desc : "SQL errors will be written to the output." },  
      { name: '#([a-zA-Z0-9_\\-\\*\\+\\.]+)',
                                    type: String,    required: false, desc : "A regular expression to replace a string with a value in the query." }, 
    ]

    The above optionDef will produce the below argv object on succesful parsing of input args array :

    --query flowstat.sql --interval 2 --count 5 --#__SOAINFRA PRFMX_SOAINFRA

    {
       "query":{
          "name":"query", "value":"flowstat.sql",
          "def":{ "name":"query", "required":true, "desc":"SQL query file.", "__use":1
          }
       },
       "interval":{
          "name":"interval", "value":2,
          "def":{ "name":"interval", "required":true, "desc":"Delay in seconds betwen iterations.", "__use":1
          }
       },
       "count":{
          "name":"count", "value":5,
          "def":{
             "name":"count", "required":true, "desc":"Number of iterations the query will run.", "__use":1
          }
       },
       "#__SOAINFRA":{
          "name":"#__SOAINFRA", "value":"PRFMX_SOAINFRA",
          "def":{ "name":"#([a-zA-Z0-9_\\-\\*\\+\\.]+)", "required":false, "desc":"A regular expression...", "__use":1
          }
       }
    }

    This library was developed as there was no other good library of similar kind that would be possible
    to use in Nashorn Javascript engine. 
*/

var ARG_PREFIX = "--";

var parseArgs = function(args, optionDefinitions) {

  function findArgDef(aName, optionDefs) {
      // find the argument in option definitions
      for (var aDef in optionDefs) 
          if (aName.match(optionDefs[aDef].name)) 
              return { name : aName, value : null, def : optionDefs[aDef] };
      return null;
  }

  var argv = {}; // result object containing parsed arguments
  var inx = 0; // index of the args array
  var exp = 0; // expected next item: 0 = argument name, 1 = argument value
  var arg = null; // current argument being parsed

  while (inx < args.length) {
    var item = args[inx];

    // expects arg name on this pposition
    if (exp === 0) {
      // parse the arg name, it must start with leading ARG_PREFIX
      if (!item.startsWith(ARG_PREFIX)) {
        // if this is not arg definition and the last arg is of type String then add this to its value
        // this is required when the arg value has spaces
        if (arg && arg.def && arg.def.type == String) 
          arg.value = !arg.value ? item : arg.value + " " + item;
        else
          throw "Argument name expected, the name '" + item + "' is invalid. The argument name must be prefixed with '" + ARG_PREFIX + "'."
      } else {

        // find the arg in option definitions
        arg = findArgDef(item.substr(ARG_PREFIX.length), optionDefinitions);

        // error when not found
        if (!arg)
          throw "Argument '" + item + "' is not defined.";

        // increase the use of the arg in options defitions
        arg.def.__use ? arg.def.__use++ : arg.def.__use = 1;

        // determine what should be next
        // if the arg is pf type switch (type == null), add arg to argv, and the next expected value is arg name
        // otherwise the next expected value is the value of the argument
        if (!arg.def.type) {
          argv[arg.name] = arg;
          arg = null;
          exp = 0;
        } else {
          exp = 1;
        }

      }
    } else

    // expects arg value on this position
    if (exp === 1) {
      // this should never happen but better check here
      if (!arg)
        throw "Internal error. The arg value is null."
      
      // the item should not start with leading ARG_PREFIX
      if (item.startsWith(ARG_PREFIX))
        // is this next argument? otherwise use this as the arg value
        if (findArgDef(item.substr(ARG_PREFIX.length), optionDefinitions) != null)
          throw "A value is missing for argument " + ARG_PREFIX + arg.def.name;
      
      // assign this item to the arg value
      // fallback to string if no type is defined
      if (!arg.def.type)
        arg.def.type = String;

      // set the value as per the type
      switch (arg.def.type) {
        case String:  
          arg.value = item; 
          break;
        
        case Number:  
          arg.value = new Number(item); 
          if (isNaN(arg.value))
            throw "The value of argument " + arg.name + " (" + item + ") is not a Number.";
          break;
        
        case Boolean: 
          arg.value = new Boolean(item); 
          break;
        
        default: arg.value = item; 
      }

      // set this param to argv
      argv[arg.name] = arg;

      // the next expected value is param name
      exp = 0;
    }

    inx++;
  }

  // check that all required params are present
  for (var aDef in optionDefinitions) {
    if (optionDefinitions[aDef].required && !optionDefinitions[aDef].__use)
      throw "Argument " + optionDefinitions[aDef].name + " is required but has not been defined.";
  }

  return argv;

}

var showArgsHelp = function(programName, optionDefs) {

  // helper functions
  // returns spaces for padding
  var space = function(an, ml) {
    var s = "";
    for (var i = 0; i < ml - (an.length + ARG_PREFIX.length); i++)
      s += " ";
    return s;
  }

  // return string representation of the type
  var type2str = function(type) {
    switch (type) {
      case String: return "string"; break;  
      case Number: return "number"; break; 
      case Boolean: return "boolean"; break; 
      default: return "n/a"; 
    }  
  }

  // writes usage on a command line
  print(programName);
  var maxl = 0;
  var usage = "Usage: ";
  for (def in optionDefs) {
    var df = optionDefs[def];
    usage += (!df.required ? "[" : "") + ARG_PREFIX + df.name + (df.type ? " <" + type2str(df.type) + ">" : "") + (!df.required ? "]" : "") + " "; 
    if (df.name.length > maxl) maxl = df.name.length;
  }
  
  print(usage);
  print("");

  // write detail help for every parameter
  print("Where: ");
  for (def in optionDefs) {
    var df = optionDefs[def];
    print("   " + ARG_PREFIX + df.name + space(df.name, maxl + 2) + " " + df.desc);
  }
}

var parseArgsAndHelp = function(programName, args, optionDefs) {
  
  var showHelp = function() {
    showArgsHelp(programName, optionDef);
    print("");
  }

  try {
    if (args[0] === ARG_PREFIX + "help") {
      showHelp();
      return null;
    } else
      return parseArgs(args, optionDef);
  } catch (e) {
    print(e); 
    print("");
    showHelp();
    return null;
  }
}

