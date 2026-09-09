using System;
using System.IO;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;
using System.Text.Json;

// Read metadata, never load or execute a candidate assembly.
using var stream = File.OpenRead(args[0]);
using var reader = new PEReader(stream);
var metadata = reader.GetMetadataReader();
Console.WriteLine(JsonSerializer.Serialize(new {
    sha256 = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(args[0]))).ToLowerInvariant(),
    mvid = metadata.GetGuid(metadata.GetModuleDefinition().Mvid).ToString()
}));
