a <- sort(gsub(".rst","",list.files(paste(getwd(),"/_autosummary",sep=""))));a
a <- paste("    ",a,sep="");a
writeLines(a, "modulesList.txt")
