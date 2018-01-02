#!/usr/bin/env cwl-runner

cwlVersion: v1.0

class: CommandLineTool

requirements:
  - class: InlineJavascriptRequirement
  - class: DockerRequirement
    dockerPull: quay.io/ncigdc/somaticsniper-tool:1.0
  - class: InitialWorkDirRequirement
    listing:
      - entry: $(inputs.vcf)
        entryname: $(inputs.vcf.basename)
        writable: True

inputs:
  vcf:
    type: File
    inputBinding:
      position: 1
      prefix: --snp-file
      valueFrom: $(self.basename)

  pileup:
    type: File
    inputBinding:
      position: 1
      prefix: --indel-file

outputs:
  output:
    type: File
    outputBinding:
      glob: $(inputs.vcf.basename + '.SNPfilter')

baseCommand: ['perl', '/home/ubuntu/bin/somatic-sniper-1.0.5.0/src/scripts/snpfilter.pl']
